# =============================================================
# Generator Kolorowanek AI
# Wersja: 1.1.0
# Data: 2025-07-09
# Opis: Nowa wersja aplikacji Streamlit do generowania czarno-białych kolorowanek
#       z wykorzystaniem DALL-E 3 i GPT-4o (OpenAI). Poprawki promptów, PDF, dokumentacji.
# =============================================================

"""
Generator Kolorowanek AI
========================

Aplikacja Streamlit do generowania czarno-białych kolorowanek dla dzieci na podstawie opisu tekstowego,
z wykorzystaniem modeli OpenAI (DALL-E 3, GPT-4o).

Autor: Alan Steinbarth
Wersja: 1.1.0
Data: 2025-07-09
Repozytorium: https://github.com/AlanSteinbarth/Kolorowanki
Licencja: MIT

Główne funkcje:
- Ulepszanie opisu przez GPT-4o (bez kolorów, dźwięków, zapachów)
- Generowanie promptu do DALL-E 3 (czarno-biały line art)
- Generowanie obrazu (1024x1024 px) i osadzanie go na białym tle A4 (PDF, poziomo)
- Pobieranie gotowego PDF bez marginesów

Wymagania: Python 3.10+, klucz OpenAI API
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
        "Jesteś kreatywnym asystentem, który pomaga tworzyć szczegółowe, ale proste opisy do kolorowanek dla dzieci. "
        "Twoim zadaniem jest wziąć temat i ogólny opis od użytkownika i przekształcić go w bardziej szczegółowy, konkretny opis sceny, "
        "który będzie idealny dla generatora czarno-białych rysunków AI. "
        "Opis powinien być prosty do zrozumienia dla dziecka, łatwy do narysowania i nie powinien zawierać żadnych odniesień do kolorów, dźwięków ani zapachów. "
        "Unikaj wszelkich metafor barwnych, opisów kolorów, efektów dźwiękowych i zapachowych. Skup się wyłącznie na kształtach, postaciach, czynnościach i prostych detalach widocznych na rysunku. "
        "Zawsze zwracaj tylko i wyłącznie ulepszony opis, bez żadnych dodatkowych komentarzy. "
        "Jeśli zabraknie miejsca na odpowiedź, zakończ ją pełnym zdaniem, nie urywaj w połowie słowa. "
        "Przykład: Użytkownik: Temat=\"Zwierzęta\", Opis=\"kot\" "
        "Ty: 'Puszysty kotek z dużymi oczami bawi się kłębkiem wełny na dywanie w pokoju.'"
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
    Generuje minimalistyczny prompt dla DALL-E na podstawie tematu i opisu.
    :param theme_val: Temat kolorowanki
    :param desc_val: Opis sceny
    :return: str (prompt)
    """
    prompt_text = (
        f"Create a black-and-white line art illustration for a children’s coloring page. "
        f"Style: simple clean outlines, no shading, no color fills, no frames or borders. "
        f"Scene: {theme_val}. {desc_val}. "
        f"White background. Output format: PNG on white canvas."
    )
    return prompt_text


# Generuje obraz za pomocą DALL-E 3 na podstawie promptu.
# Zwraca (url, None) lub (None, komunikat o błędzie).
def generate_image(prompt_val, openai_key):
    """
    Generuje obraz za pomocą DALL-E 3 na podstawie promptu (1024x1024 px).
    :param prompt_val: Prompt tekstowy
    :param openai_key: Klucz API OpenAI
    :return: (str lub None, str lub None)
    """
    openai.api_key = openai_key
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt_val,
            size="1024x1024",  # kwadratowy format
            quality="standard",
            n=1,
        )
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
    Tworzy plik PDF z wygenerowanego obrazka, umieszczając go na białym tle A4 (poziomo, 300 DPI).
    :param image_url: URL do obrazka
    :return: (bytes lub None, str lub None)
    """
    try:
        response = requests.get(image_url, timeout=10)
        img_data = BytesIO(response.content)
        with Image.open(img_data) as img:
            img = img.convert("RGB")
            # Ustawienia A4 poziomo w pikselach (300 DPI): 3508x2480
            a4_w, a4_h = 3508, 2480
            canvas = Image.new("RGB", (a4_w, a4_h), "white")
            # Przeskaluj wygenerowany kwadrat, by wypełnił możliwie szeroko:
            w, h = img.size
            new_w = a4_w
            new_h = int(h * (a4_w / w))
            # Ustal odpowiedni filtr resamplingu (kompatybilność z różnymi wersjami Pillow)
            try:
                resample_filter = Image.Resampling.LANCZOS
            except AttributeError:
                try:
                    resample_filter = getattr(Image, "LANCZOS", None)
                    if resample_filter is None:
                        raise AttributeError
                except AttributeError:
                    resample_filter = 1  # 1 = LANCZOS w Pillow
            if new_h < a4_h:
                resized = img.resize((new_w, new_h), resample_filter)
            else:
                new_h = a4_h
                new_w = int(w * (a4_h / h))
                resized = img.resize((new_w, new_h), resample_filter)
            # Wycentruj na białym tle
            x = (a4_w - resized.width) // 2
            y = (a4_h - resized.height) // 2
            canvas.paste(resized, (x, y))
            # Zapisz do pliku tymczasowego
            temp_path = "temp_coloring.png"
            canvas.save(temp_path, format="PNG")

        pdf = FPDF(orientation="L", unit="mm", format="A4")
        pdf.add_page()
        # Wymiary A4 poziomo: 297 x 210 mm
        pdf.image(temp_path, x=0, y=0, w=297, h=210)
        os.remove(temp_path)
        pdf_str = pdf.output(dest='S')
        if isinstance(pdf_str, str):
            pdf_output = pdf_str.encode('latin1')
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
st.title("🎨 Generator Kolorowanek AI 🤖")
st.write('''
Aplikacja do generowania kolorowanek dla dzieci przy wykorzystaniu AI (DALL-E 3, GPT-4o).
''')


# --- Sidebar - Klucz API ---
# Wprowadzenie klucza API OpenAI
api_key_input = st.sidebar.text_input(
    "Wpisz klucz API OpenAI", type="password",
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
    if st.button("Wygeneruj kolorowankę 🖍️"):
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

# =====================
# Autor: Alan Steinbarth
# =====================

