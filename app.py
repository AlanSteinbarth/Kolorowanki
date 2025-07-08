import streamlit as st
import openai
import os
from dotenv import load_dotenv
from fpdf import FPDF
import requests
from io import BytesIO
from PIL import Image

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

def enhance_description_with_ai(theme, description, api_key):
    """Używa modelu językowego do wzbogacenia opisu użytkownika."""
    try:
        openai.api_key = api_key
        system_prompt = """
        Jesteś kreatywnym asystentem, który pomaga tworzyć szczegółowe opisy do kolorowanek dla dzieci.
        Twoim zadaniem jest wziąć temat i ogólny opis od użytkownika i przekształcić go w bardziej barwny,
        szczegółowy i konkretny opis sceny, który będzie idealny dla generatora obrazów AI.
        Opis powinien być prosty do zrozumienia dla dziecka i łatwy do narysowania.
        Zawsze zwracaj tylko i wyłącznie ulepszony opis, bez żadnych dodatkowych komentarzy.
        Przykład:
        Użytkownik: Temat="Zwierzęta", Opis="kot"
        Ty: "Uroczy, puszysty kotek z dużymi oczami bawi się kłębkiem wełny na miękkim dywanie w przytulnym pokoju."
        """
        user_prompt = f"Temat: '{theme}', Opis: '{description}'"

        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=150
        )
        enhanced_description = response.choices[0].message.content.strip()
        return enhanced_description, None
    except Exception as e:
        return None, f"Błąd podczas ulepszania opisu: {e}"

def generate_coloring_page_prompt(theme, description):
    """Generuje prompt dla DALL-E na podstawie tematu i opisu."""
    prompt = (
        f"Stwórz stronę do kolorowania dla dzieci. Obrazek musi być wyłącznie czarno-biały, "
        f"z grubymi, wyraźnymi konturami na czystym białym tle. "
        f"Zabronione jest używanie jakichkolwiek kolorów, szarości, cieniowania, wypełnień, "
        f"gradientów, tekstur, półtonów i wszelkich odcieni innych niż czysta czerń i biel. "
        f"Tylko kontury i linie. "
        f"Obrazek musi być w formacie poziomym, proporcje i kompozycja idealnie dopasowane do kartki A4 w układzie poziomym (297x210mm, 1792x1024px). "
        f"Wypełnij całą kartkę rysunkiem, nie zostawiaj pustych marginesów. "
        f"Temat: {theme}. Opis: {description}. Styl: prosta kreskówka."
    )
    return prompt

def generate_image(prompt, api_key):
    """Generuje obraz za pomocą DALL-E."""
    openai.api_key = api_key
    try:
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",  # Zmieniono na kwadratowy, obsługiwany rozmiar
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url
        return image_url, None
    except Exception as e:
        return None, f"Błąd podczas generowania obrazu: {e}"

def create_pdf(image_url):
    """Tworzy plik PDF z wygenerowanego obrazka w poziomym układzie A4."""
    try:
        response = requests.get(image_url)
        img_data = BytesIO(response.content)
        # Zapisz obraz tymczasowo na dysku, bo FPDF nie obsługuje obiektów Pillow ani BytesIO
        with Image.open(img_data) as image:
            temp_path = "temp_coloring.png"
            image.save(temp_path, format="PNG")

        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        # Wymiary A4 poziomo: 297 x 210 mm
        page_width = 297
        page_height = 210
        # Ustal szerokość i wysokość obrazu, aby zachować proporcje i nie wychodzić poza marginesy
        img_width = page_width - 20  # 10 mm marginesu z każdej strony
        img_height = page_height - 20
        # Wstaw obraz na środek strony
        x_pos = (page_width - img_width) / 2
        y_pos = (page_height - img_height) / 2
        pdf.image(temp_path, x=x_pos, y=y_pos, w=img_width, h=img_height)
        # Usuń plik tymczasowy
        os.remove(temp_path)
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
        pdf_bytes, error = create_pdf(st.session_state.image_url)
        if error:
            st.error(error)
        else:
            st.download_button(
                label="Pobierz jako PDF",
                data=pdf_bytes,
                file_name=f"kolorowanka_{st.session_state.theme.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
    
    st.write("Nie jesteś zadowolony z wyniku? Zmień opis i wygeneruj ponownie.")

