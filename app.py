
"""Aplikacja Streamlit do generowania kolorowanek AI (DALL-E 3, GPT-4o)."""

import os
from io import BytesIO
import streamlit as st
import openai
from dotenv import load_dotenv
from fpdf import FPDF
import requests
from PIL import Image


# --- Konfiguracja ---
load_dotenv()

# --- Funkcje pomocnicze ---

def check_api_key(openai_key):
    """Sprawdza poprawność klucza API OpenAI."""
    openai.api_key = openai_key
    try:
        openai.models.list()
        return True, "Klucz API jest poprawny."
    except openai.AuthenticationError:
        return False, "Błąd uwierzytelniania. Sprawdź swój klucz API."
    except Exception as exc:
        return False, f"Wystąpił nieoczekiwany błąd: {exc}"


def enhance_description_with_ai(theme_val, desc_val, openai_key):
    """Używa modelu językowego do wzbogacenia opisu użytkownika."""
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
    except Exception as exc:
        return None, f"Błąd podczas ulepszania opisu: {exc}"

def generate_coloring_page_prompt(theme_val, desc_val):
    """Generuje prompt dla DALL-E na podstawie tematu i opisu."""
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

def generate_image(prompt_val, openai_key):
    """Generuje obraz za pomocą DALL-E."""
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

def create_pdf(image_url):
    """Tworzy plik PDF z wygenerowanego obrazka w poziomym układzie A4."""
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
        # FPDF.output(dest='S') zwraca już bytes (bytearray)
        pdf_output = bytes(pdf.output(dest='S'))
        return pdf_output, None
    except Exception as exc:
        return None, f"Błąd podczas tworzenia PDF: {exc}"


# --- Interfejs użytkownika Streamlit ---

st.set_page_config(page_title="Generator Kolorowanek AI", layout="centered")

st.title("🎨 Generator Kolorowanek AI")
st.write('''
Aplikacja do generowania kolorowanek dla dzieci przy wykorzystaniu AI. 
''')

# --- Sidebar - Klucz API ---
st.sidebar.header("Konfiguracja")
api_key_input = st.sidebar.text_input("Klucz API OpenAI", type="password", help="Wpisz swój klucz API lub upewnij się, że jest w pliku .env")

api_key = api_key_input or os.getenv("OPENAI_API_KEY")

if not api_key:
    st.warning("Wprowadź klucz API OpenAI w panelu bocznym, aby rozpocząć.")
    st.stop()

is_key_valid, message = check_api_key(api_key)
if is_key_valid:
    st.sidebar.success(message)
else:
    st.sidebar.error(message)
    st.stop()

# --- Główny interfejs ---
st.header("1. Opisz swoją kolorowankę")

# Inicjalizacja stanu sesji
if 'description_text' not in st.session_state:
    st.session_state.description_text = ""
if 'generated_prompt' not in st.session_state:
    st.session_state.generated_prompt = None

theme = st.text_input("Temat kolorowanki", placeholder="np. leśne zwierzęta, pojazdy kosmiczne")

# Pole tekstowe, którego zawartość jest kontrolowana przez stan sesji
description = st.text_area(
    "Co ma zawierać kolorowanka?",
    value=st.session_state.description_text,
    placeholder="np. uśmiechnięty lew bawiący się piłką w dżungli",
    key="description_area",
    height=250
)
st.session_state.description_text = description # Synchronizacja po ewentualnej edycji przez użytkownika

col1, col2 = st.columns(2)

with col1:
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
                    st.session_state.generated_prompt = None # Resetuj prompt po zmianie opisu
                    st.rerun()

with col2:
    if st.button("Wygeneruj kolorowankę 🎨"):
        if not theme or not description:
            st.error("Wypełnij temat i opis, aby wygenerować kolorowankę.")
        else:
            with st.spinner("Sztuczna inteligencja tworzy Twoją kolorowankę..."):
                final_description = description
                
                prompt = generate_coloring_page_prompt(theme, final_description)
                st.session_state.generated_prompt = prompt # Zapisz prompt do stanu sesji

                image_url, error = generate_image(prompt, api_key)
                if error:
                    st.error(error)
                else:
                    st.session_state.image_url = image_url
                    st.session_state.theme = theme
                    st.rerun()

# Wyświetlanie promptu w pełnej szerokości, jeśli istnieje
if st.session_state.get('generated_prompt'):
    st.info(f"**Wygenerowany prompt:**\n{st.session_state.generated_prompt}")

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

