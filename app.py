import streamlit as st
import openai
import os
from dotenv import load_dotenv
from fpdf import FPDF
import requests
from io import BytesIO

# --- Konfiguracja ---
load_dotenv()

# --- Funkcje pomocnicze ---

def check_api_key(api_key):
    """Sprawdza poprawność klucza API OpenAI."""
    openai.api_key = api_key
    try:
        openai.models.list()
        return True, "Klucz API jest poprawny."
    except openai.AuthenticationError:
        return False, "Błąd uwierzytelniania. Sprawdź swój klucz API."
    except Exception as e:
        return False, f"Wystąpił nieoczekiwany błąd: {e}"

def generate_coloring_page_prompt(description):
    """Generuje prompt dla DALL-E na podstawie opisu."""
    prompt = f"Stwórz prostą, czarno-białą kolorowankę dla dzieci. Obrazek powinien mieć wyraźne, grube kontury i być łatwy do pokolorowania. Opis: {description}. Styl: kreskówka, bez cieni, czyste linie."
    return prompt

def generate_image(prompt, api_key):
    """Generuje obraz za pomocą DALL-E."""
    openai.api_key = api_key
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url, None
    except Exception as e:
        return None, f"Błąd podczas generowania obrazu: {e}"

def create_pdf(image_url):
    """Tworzy plik PDF z wygenerowanego obrazka."""
    try:
        response = requests.get(image_url)
        img_data = BytesIO(response.content)
        
        pdf = FPDF(orientation='P', unit='mm', format='A4')
        pdf.add_page()
        # Szerokość obrazu w mm (A4 ma 210mm szerokości)
        img_width = 190 
        # Centralizacja obrazu
        x_pos = (210 - img_width) / 2
        pdf.image(img_data, x=x_pos, y=10, w=img_width, type='PNG')
        
        # Zapis do bufora w pamięci
        pdf_output = pdf.output(dest='S').encode('latin-1')
        return pdf_output, None
    except Exception as e:
        return None, f"Błąd podczas tworzenia PDF: {e}"


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

description = st.text_area("Co ma zawierać kolorowanka?", placeholder="np. uśmiechnięty lew bawiący się piłką w dżungli")

if st.button("Wygeneruj kolorowankę"):
    if not description:
        st.error("Wypełnij opis, aby wygenerować kolorowankę.")
    else:
        with st.spinner("Sztuczna inteligencja tworzy Twoją kolorowankę..."):
            # 1. Generowanie promptu
            prompt = generate_coloring_page_prompt(description)
            st.info(f"**Wygenerowany prompt:**\n{prompt}")

            # 2. Generowanie obrazu
            image_url, error = generate_image(prompt, api_key)
            if error:
                st.error(error)
            else:
                st.session_state.image_url = image_url
                st.session_state.description = description # Zapisujemy opis do późniejszego wykorzystania

if "image_url" in st.session_state:
    st.header("2. Twoja kolorowanka jest gotowa!")
    st.image(st.session_state.image_url, caption="Wygenerowana kolorowanka")

    st.header("3. Pobierz lub popraw")
    
    # Pobieranie PDF
    with st.spinner("Przygotowuję plik PDF..."):
        pdf_bytes, error = create_pdf(st.session_state.image_url)
        if error:
            st.error(error)
        else:
            st.download_button(
                label="Pobierz jako PDF",
                data=pdf_bytes,
                file_name=f"kolorowanka.pdf",
                mime="application/pdf"
            )
    
    st.write("Nie jesteś zadowolony z wyniku? Zmień opis i wygeneruj ponownie.")

