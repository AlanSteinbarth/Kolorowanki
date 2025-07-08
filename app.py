

# =============================================================
# Generator Kolorowanek AI
# Wersja: 1.0.0
# Autor: Alan Steinbarth
# Data: 2025-07-08
# Opis: Aplikacja Streamlit do generowania czarno-białych kolorowanek
#       z wykorzystaniem DALL-E 3 i GPT-4o (OpenAI).
# =============================================================

"""
# Generator Kolorowanek AI
#
# Aplikacja Streamlit do generowania czarno-białych kolorowanek dla dzieci
# na podstawie opisu tekstowego, z użyciem modeli OpenAI (DALL-E 3, GPT-4o).
#
# Autor: Alan Steinbarth
# Wersja: 1.0.0
# Repozytorium: https://github.com/AlanSteinbarth/Kolorowanki
"""



import os
import tempfile
from io import BytesIO

import requests
import streamlit as st
import openai
from dotenv import load_dotenv
from fpdf import FPDF
from PIL import Image



# =====================
# KONFIGURACJA I IMPORTY
# =====================

load_dotenv()  # Wczytaj zmienne środowiskowe z pliku .env


# =====================
# FUNKCJE POMOCNICZE (AI, PDF, PROMPT)
# =====================


# Sprawdza poprawność klucza API OpenAI.
# Zwraca (True, komunikat) jeśli OK, w przeciwnym razie (False, komunikat).
def check_api_key(openai_key: str) -> tuple[bool, str]:
    """
    Sprawdza poprawność klucza API OpenAI.
    :param openai_key: Klucz API OpenAI
    :return: (bool, str) - czy klucz jest poprawny, komunikat
    """
    openai.api_key = openai_key
    try:
        openai.models.list()
        return True, "Klucz API jest poprawny."
    except openai.AuthenticationError:
        return False, "Błąd uwierzytelniania. Sprawdź swój klucz API."
    except Exception as exc:  # pylint: disable=broad-except
        return False, f"Wystąpił nieoczekiwany błąd: {exc}"



# Ulepsza opis użytkownika za pomocą GPT-4o.
# Zwraca (opis, None) lub (None, komunikat o błędzie).
def enhance_description_with_ai(theme_val: str, desc_val: str, openai_key: str) -> tuple[str | None, str | None]:
    """
    Ulepsza opis użytkownika za pomocą GPT-4o.
    :param theme_val: Temat kolorowanki
    :param desc_val: Opis sceny
    :param openai_key: Klucz API OpenAI
    :return: (str lub None, str lub None)
    """
    openai.api_key = openai_key
    system_prompt = (
        "Jesteś kreatywnym asystentem, który pomaga tworzyć szczegółowe opisy do kolorowanek dla dzieci. "
        "Twoim zadaniem jest wziąć temat i ogólny opis od użytkownika i przekształcić go w bardziej barwny, "
        "szczegółowy i konkretny opis sceny, który będzie idealny dla generatora obrazów AI. "
        "Opis powinien być prosty do zrozumienia dla dziecka i łatwy do narysowania. "
        "Zawsze zwracaj tylko i wyłącznie ulepszony opis, bez żadnych dodatkowych komentarzy. "
        "Przykład: Użytkownik: Temat=\"Zwierzęta\", Opis=\"kot\" "
        "Ty: 'Uroczy, puszysty kotek z dużymi oczami bawi się kłębkiem wełny na miękkim dywanie w przytulnym pokoju.'"
    )
    user_prompt = f"Temat: '{theme_val}', Opis: '{desc_val}'"
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        choices = getattr(response, "choices", None)
        if not choices or not choices[0].message or not getattr(choices[0].message, "content", None):
            return None, "Błąd: Brak odpowiedzi z AI. Spróbuj ponownie."
        enhanced_description = choices[0].message.content
        if enhanced_description:
            return enhanced_description.strip(), None
        return None, "Błąd: Odpowiedź AI jest pusta."
    except openai.OpenAIError as exc:
        return None, f"Błąd OpenAI: {exc}"
    except Exception as exc:  # pylint: disable=broad-except
        return None, f"Błąd podczas ulepszania opisu: {exc}"


# Generuje prompt dla DALL-E na podstawie tematu i opisu.
# Zwraca gotowy prompt tekstowy.
def generate_coloring_page_prompt(theme_val: str, desc_val: str) -> str:
    """
    Generuje prompt dla DALL-E na podstawie tematu i opisu.
    :param theme_val: Temat kolorowanki
    :param desc_val: Opis sceny
    :return: str (prompt)
    """
    prompt_text = (
        f"Stwórz stronę do kolorowania dla dzieci. Obrazek musi być wyłącznie czarno-biały, "
        f"z grubymi, wyraźnymi konturami na czystym białym tle. "
        f"Zabronione jest używanie jakichkolwiek kolorów, szarości, cieniowania, wypełnień, "
        f"gradientów, tekstur, półtonów i wszelkich odcieni innych niż czysta czerń i biel. "
        f"Tylko kontury i linie. "
        f"Obrazek musi być w formacie poziomym, proporcje i kompozycja idealnie dopasowane do kartki A4 w układzie poziomym (297x210mm, 1792x1024px). "
        f"Wypełnij całą kartkę rysunkiem, nie zostawiaj pustych marginesów. "
        f"Temat: {theme_val}. Opis: {desc_val}. Styl: prosta kreskówka."
    )
    return prompt_text


# Generuje obraz za pomocą DALL-E 3 na podstawie promptu.
# Zwraca (url, None) lub (None, komunikat o błędzie).
def generate_image(prompt_val: str, openai_key: str) -> tuple[str | None, str | None]:
    """
    Generuje obraz za pomocą DALL-E 3 na podstawie promptu.
    :param prompt_val: Prompt tekstowy
    :param openai_key: Klucz API OpenAI
    :return: (str lub None, str lub None)
    """
    openai.api_key = openai_key
    # Walidacja promptu
    if not prompt_val or len(prompt_val.strip()) < 30:
        return None, "Prompt jest zbyt krótki lub pusty. Opisz dokładniej swoją kolorowankę."
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt_val,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        data = getattr(response, "data", None)
        if not data or not data[0] or not getattr(data[0], "url", None):
            return None, "Błąd: Brak obrazu z DALL-E. Spróbuj ponownie."
        image_url_val = data[0].url
        return image_url_val, None
    except openai.OpenAIError as exc:
        return None, f"Błąd OpenAI: {exc}"
    except requests.RequestException as exc:
        return None, f"Błąd sieci: {exc}"
    except Exception as exc:  # pylint: disable=broad-except
        return None, f"Błąd podczas generowania obrazu: {exc}"


# Tworzy plik PDF z wygenerowanego obrazka w poziomym układzie A4.
# Zwraca (bytes, None) lub (None, komunikat o błędzie).
def create_pdf(img_url: str) -> tuple[bytes | None, str | None]:
    """
    Tworzy plik PDF z wygenerowanego obrazka w poziomym układzie A4.
    :param img_url: URL do obrazka
    :return: (bytes lub None, str lub None)
    """
    try:
        response = requests.get(img_url, timeout=10)
        img_data = BytesIO(response.content)
        with Image.open(img_data) as img:
            img = img.convert("RGB")
            a4_ratio = 297 / 210
            img_ratio = img.width / img.height
            if img_ratio > a4_ratio:
                new_height = 1024
                new_width = int(new_height * a4_ratio)
            else:
                new_width = 1792
                new_height = int(new_width / a4_ratio)
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError as exc:
                try:
                    resample_filter = getattr(Image, "LANCZOS", None)
                    if resample_filter is None:
                        raise AttributeError from exc
                except AttributeError:
                    resample_filter = 1
            img_resized = img.resize((new_width, new_height), resample_filter)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                temp_path = tmp_file.name
                img_resized.save(temp_path, format="PNG")

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        page_width = 297
        page_height = 210
        pdf.image(temp_path, x=0, y=0, w=page_width, h=page_height)
        os.remove(temp_path)
        pdf_raw = pdf.output(dest='S')
        if isinstance(pdf_raw, str):
            pdf_output = pdf_raw.encode('latin1')
        elif isinstance(pdf_raw, (bytes, bytearray)):
            pdf_output = bytes(pdf_raw)
        else:
            return None, "Nieoczekiwany format danych PDF."
        return pdf_output, None
    except Exception as exc:  # pylint: disable=broad-except
        return None, f"Błąd podczas tworzenia PDF: {exc}"



# =====================
# INTERFEJS UŻYTKOWNIKA STREAMLIT
# =====================


# Konfiguracja strony
st.set_page_config(page_title="Generator Kolorowanek AI", layout="centered")



# Nagłówek i opis
st.title("🎨 Generator Kolorowanek AI")
st.write('''
Aplikacja do generowania kolorowanek dla dzieci przy wykorzystaniu AI (DALL-E 3, GPT-4o).
''')



# --- Sidebar - Klucz API ---
st.sidebar.header("Konfiguracja")
# Wprowadzenie klucza API OpenAI
api_key_input = st.sidebar.text_input(
    "Klucz API OpenAI", type="password",
    help="Wpisz swój klucz API lub upewnij się, że jest w pliku .env"
)
api_key = api_key_input or os.getenv("OPENAI_API_KEY")
if not api_key:
    st.warning("Wprowadź klucz API OpenAI w panelu bocznym, aby rozpocząć.")
    st.stop()
# Weryfikacja klucza API
is_key_valid, message = check_api_key(api_key)
if is_key_valid:
    st.sidebar.success(message)
else:
    st.sidebar.error(message)
    st.stop()


# =====================
# GŁÓWNY INTERFEJS UŻYTKOWNIKA
# =====================

# Sekcja: Opis kolorowanki
st.header("1. Opisz swoją kolorowankę")

# Inicjalizacja stanu sesji (opis i prompt)
if 'description_text' not in st.session_state:
    st.session_state.description_text = ""
if 'generated_prompt' not in st.session_state:
    st.session_state.generated_prompt = None

# Pole: Temat kolorowanki
theme = st.text_input(
    "Temat kolorowanki",
    placeholder="np. leśne zwierzęta, pojazdy kosmiczne"
)

# Pole: Opis kolorowanki (kontrolowane przez stan sesji)
description = st.text_area(
    "Co ma zawierać kolorowanka?",
    value=st.session_state.description_text,
    placeholder="np. uśmiechnięty lew bawiący się piłką w dżungli",
    key="description_area",
    height=250
)
st.session_state.description_text = description  # Synchronizacja po edycji

# Przyciski: Ulepsz opis i Wygeneruj kolorowankę

# Przyciski: Ulepsz opis (lewo) i Wygeneruj kolorowankę (prawo)
left_col, spacer, right_col = st.columns([1, 2, 1])

with left_col:
    if st.button("Ulepsz opis ✨"):
        if not theme or not description:
            st.error("Wypełnij temat i opis, aby go ulepszyć.")
        else:
            with st.spinner("AI ulepsza Twój opis..."):
                enhanced_desc, error = enhance_description_with_ai(theme, description, api_key)
                if error:
                    st.error(error)
                else:
                    st.session_state.description_text = enhanced_desc
                    st.session_state.generated_prompt = None
                    st.rerun()

with right_col:
    if st.button("Wygeneruj kolorowankę 🎨"):
        if not theme or not description:
            st.error("Wypełnij temat i opis, aby wygenerować kolorowankę.")
        else:
            with st.spinner("Sztuczna inteligencja tworzy Twoją kolorowankę..."):
                final_description = description
                prompt = generate_coloring_page_prompt(theme, final_description)
                st.session_state.generated_prompt = prompt
                image_url, error = generate_image(prompt, api_key)
                if error:
                    st.error(error)
                else:
                    st.session_state.image_url = image_url
                    st.session_state.theme = theme
                    st.rerun()

# Sekcja: Wyświetlanie promptu
if st.session_state.get('generated_prompt'):
    st.info(f"**Wygenerowany prompt:**\n{st.session_state.generated_prompt}")

# Sekcja: Wyświetlanie i pobieranie kolorowanki
if "image_url" in st.session_state:
    st.header("2. Twoja kolorowanka jest gotowa!")
    st.image(st.session_state.image_url, caption="Wygenerowana kolorowanka")
    # Pobieranie PDF
    with st.spinner("Przygotowuję plik PDF..."):
        pdf_bytes, pdf_error = create_pdf(st.session_state.image_url)
        if pdf_error or not pdf_bytes:
            st.error(pdf_error or "Nie udało się wygenerować pliku PDF.")
        else:
            st.download_button(
                label="Pobierz jako PDF",
                data=pdf_bytes,
                file_name=f"kolorowanka_{st.session_state.theme.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
    st.write("Nie jesteś zadowolony z wyniku? Zmień opis i wygeneruj ponownie.")

