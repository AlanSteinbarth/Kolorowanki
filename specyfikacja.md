# Projekt: Kolorowanki

## Opis

Aplikacja do generowania kolorowanek dla dzieci przy wykozystaniu AI. Prosta aplikacja. "im mniej tym wiecej". Bez ozdobników, upiększe, emoji. Prosta. surowa. Funkcjonalna.

## Opis działania programu

- program weryfikuje czy jest plik .env z kluczem API OpenAI lub w saidbarze w streamlit podajemy klucz API OpenAI
- program wysyła pytanie do OpenAI i sprawdza czy klucz jest poprawny. Jeśli tak to uruchamia się dalsza część programu w głównym ekranie
- mamy pełną obsługę błędów klucza API OneAI, z komunikatami typu "nieprawidłowy klucz", "brak środków na koncie" itd.
- wpisujemy temat kolorowanki
- poniej wpisujemy opis, co ma zawierać kolorowanka
- model językowy OpenAI weryfikuje czy opis kolorowanki jest kompletny. Jeśli nie, to zadaje pytanie, aby doprezyzować dane techniczne kolorowanki, np. rozmiar (A5, A4, A3) w poziomie lub pionie itd.
- program generuje propozycję kolorowanki i wyświetla ją na ekranie
- następnie mozemy odrazu pobrać kolorowankę w formacie PDF lub doc
- lub jeśli kolorowanka nie spełnia naszych oczekiwań, to wprowadzamy doprezyzowanie i generujemy poprawioną wersję kolorowanki


## Technologie

- Streamlit
- OpenAI
- PDF

## Instalacja

1.  Sklonuj repozytorium: `git clone https://github.com/AlanSteinbarth/Kolorowanki.git`




## Repozytorium GitHub

https://github.com/AlanSteinbarth/Kolorowanki
