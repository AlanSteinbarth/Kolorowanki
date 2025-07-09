

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
from io import BytesIO
import streamlit as st
import openai
from dotenv import load_dotenv
from fpdf import FPDF
import requests
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
def check_api_key(openai_key):
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
    except Exception as exc:
        return False, f"Wystąpił nieoczekiwany błąd: {exc}"



# Ulepsza opis użytkownika za pomocą GPT-4o.
# Zwraca (opis, None) lub (None, komunikat o błędzie).
def enhance_description_with_ai(theme_val, desc_val, openai_key):
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
        "Jeśli zabraknie miejsca na odpowiedź, zakończ ją pełnym zdaniem, nie urywaj w połowie słowa. "
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
            max_tokens=300  # zwiększono limit tokenów
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
    except Exception as exc:
        return None, f"Błąd podczas ulepszania opisu: {exc}"


# Generuje prompt dla DALL-E na podstawie tematu i opisu.
# Zwraca gotowy prompt tekstowy.
def generate_coloring_page_prompt(theme_val, desc_val):
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
def generate_image(prompt_val, openai_key):
    """
    Generuje obraz za pomocą DALL-E 3 na podstawie promptu.
    :param prompt_val: Prompt tekstowy
    :param openai_key: Klucz API OpenAI
    :return: (str lub None, str lub None)
    """
    openai.api_key = openai_key
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt_val,
            size="1024x1024",  # Zmieniono na kwadratowy, obsługiwany rozmiar
            quality="standard",
            n=1,
        )
        # Bezpieczne pobranie url
        data = getattr(response, "data", None)
        if not data or not data[0] or not getattr(data[0], "url", None):
            return None, "Błąd: Brak obrazu z DALL-E. Spróbuj ponownie."
        image_url_val = data[0].url
        return image_url_val, None
    except Exception as exc:
        return None, f"Błąd podczas generowania obrazu: {exc}"


# Tworzy plik PDF z wygenerowanego obrazka w poziomym układzie A4.
# Zwraca (bytes, None) lub (None, komunikat o błędzie).
def create_pdf(image_url):
    """
    Tworzy plik PDF z wygenerowanego obrazka w poziomym układzie A4.
    :param image_url: URL do obrazka
    :return: (bytes lub None, str lub None)
    """
    try:
        response = requests.get(image_url, timeout=10)
        img_data = BytesIO(response.content)
        # Zapisz obraz tymczasowo na dysku, bo FPDF nie obsługuje obiektów Pillow ani BytesIO
        with Image.open(img_data) as img:
            temp_path = "temp_coloring.png"
            img = img.convert("RGB")
            # Przeskaluj do poziomego A4 (proporcje 297x210)
            a4_ratio = 297 / 210
            img_ratio = img.width / img.height
            if img_ratio > a4_ratio:
                # Obraz za szeroki – dopasuj wysokość
                new_height = 1024
                new_width = int(new_height * a4_ratio)
            else:
                # Obraz za wysoki – dopasuj szerokość
                new_width = 1792
                new_height = int(new_width / a4_ratio)
            # Kompatybilność z różnymi wersjami Pillow
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                try:
                    resample_filter = getattr(Image, "LANCZOS", None)
                    if resample_filter is None:
                        raise AttributeError
                except AttributeError:
                    resample_filter = 1  # 1 = LANCZOS w Pillow
            img_resized = img.resize((new_width, new_height), resample_filter)
            img_resized.save(temp_path, format="PNG")

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        # Wymiary A4 poziomo: 297 x 210 mm
        page_width = 297
        page_height = 210
        # Wstaw obraz na całą stronę bez marginesów
        pdf.image(temp_path, x=0, y=0, w=page_width, h=page_height)
        os.remove(temp_path)
        # FPDF.output(dest='S') może zwracać str (wtedy trzeba zakodować na bytes)
        pdf_str = pdf.output(dest='S')
        if isinstance(pdf_str, str):
            pdf_output = pdf_str.encode('latin1')  # FPDF używa latin1
        else:
            pdf_output = pdf_str
        return pdf_output, None
    except Exception as exc:
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
    height=195,  # pośrednia wysokość
    # brak ograniczenia znaków
)
st.session_state.description_text = description  # Synchronizacja po edycji

# Przyciski: Ulepsz opis i Wygeneruj kolorowankę
col1, col2 = st.columns(2)

with col1:
    # Ulepszanie opisu przez AI
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
                    st.session_state.generated_prompt = None  # Resetuj prompt po zmianie opisu
                    st.rerun()

with col2:
    # Generowanie kolorowanki przez AI
    if st.button("Wygeneruj kolorowankę 🎨"):
        if not theme or not description:
            st.error("Wypełnij temat i opis, aby wygenerować kolorowankę.")
        else:
            with st.spinner("Sztuczna inteligencja tworzy Twoją kolorowankę..."):
                final_description = description
                prompt = generate_coloring_page_prompt(theme, final_description)
                st.session_state.generated_prompt = prompt  # Zapisz prompt do stanu sesji
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

