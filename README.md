# Generator Kolorowanek AI

Aplikacja Streamlit do generowania czarno-białych kolorowanek dla dzieci z wykorzystaniem modeli OpenAI (DALL-E 3 oraz GPT-4o).

## Opis projektu

Ten projekt umożliwia każdemu użytkownikowi szybkie tworzenie oryginalnych kolorowanek na podstawie własnego pomysłu. Wystarczy podać temat i krótki opis sceny, a aplikacja:
- opcjonalnie ulepszy opis za pomocą GPT-4o,
- wygeneruje prompt i przekaże go do DALL-E 3,
- stworzy czarno-biały, panoramiczny rysunek do kolorowania,
- umożliwi pobranie gotowej kolorowanki w formacie PDF (A4 poziomo, bez marginesów).

## Najważniejsze cechy
- **Czysto czarno-białe rysunki** – bez cieni, szarości, kolorów, wypełnień i marginesów.
- **Prosty, funkcjonalny interfejs** – tylko to, co potrzebne do generowania i pobierania kolorowanek.
- **Ulepszanie opisu przez AI** – jedno kliknięcie i Twój pomysł staje się bardziej szczegółowy i inspirujący.
- **Plik PDF gotowy do druku** – idealny do domowego użytku, zajęć edukacyjnych lub prezentu.

## Jak uruchomić?
1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/AlanSteinbarth/Kolorowanki.git
   cd Kolorowanki
   ```
2. Zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```
3. Utwórz plik `.env` i dodaj swój klucz API OpenAI:
   ```env
   OPENAI_API_KEY=sk-...
   ```
4. Uruchom aplikację:
   ```bash
   streamlit run app.py
   ```

## Portfolio
Ten projekt jest częścią mojego portfolio programistycznego. Pokazuje praktyczne wykorzystanie AI, integrację z API, obsługę PDF oraz projektowanie prostych, użytecznych interfejsów w Pythonie.

Zachęcam do kontaktu i współpracy!

---
Autor: Alan Steinbarth
