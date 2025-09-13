# Vercel Serverless Function for Translation
# This file serves as a proxy for the MyMemory API, compatible with LibreTranslate endpoint structure.
# It uses Flask for handling HTTP requests.

from flask import Flask, request, jsonify
import json
import requests
import urllib.parse

app = Flask(__name__)

# A simple in-memory cache to store translated text and avoid redundant API calls
CACHE = {}
# A list of supported languages as provided by MyMemory API (and simplified for our use case)
SUPPORTED_LANGS = ['vi', 'en', 'ru', 'zh', 'ko', 'ja', 'pt', 'es']

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """
    Handles translation requests via a POST method.
    It expects a JSON payload with 'q', 'source', and 'target' fields.
    """
    try:
        # Get the JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        # Extract the required fields, with default values if not present
        text_to_translate = data.get('q', '')
        source_lang = data.get('source', 'vi')
        target_lang = data.get('target', 'en')

        # Simple validation
        if not text_to_translate:
            return jsonify({"error": "Text to translate is empty"}), 400
        if target_lang not in SUPPORTED_LANGS:
            return jsonify({"error": f"Target language '{target_lang}' is not supported"}), 400
        
        # Construct a unique cache key for the request
        cache_key = f"{text_to_translate}:{source_lang}:{target_lang}"
        if cache_key in CACHE:
            return jsonify({"translatedText": CACHE[cache_key]})

        # LibreTranslate-compatible API call to MyMemory
        api_url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text_to_translate)}&langpair={source_lang}|{target_lang}"
        
        response = requests.get(api_url)
        response.raise_for_status()  # Raise an exception for bad status codes

        translation_data = response.json()
        translated_text = translation_data['responseData']['translatedText']

        if not translated_text:
            # Fallback mechanism if no translation is returned
            translated_text = text_to_translate

        # Cache the result before returning
        CACHE[cache_key] = translated_text
        return jsonify({"translatedText": translated_text})

    except requests.exceptions.RequestException as e:
        # Handle network or API-related errors
        print(f"API request error: {e}")
        return jsonify({"error": "Failed to connect to the translation API"}), 500
    except KeyError:
        # Handle unexpected API response format
        return jsonify({"error": "Unexpected response format from translation API"}), 500
    except Exception as e:
        # Catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

# The handler function is the entry point for Vercel
# It should not be modified, Flask handles the rest.
if __name__ == '__main__':
    app.run(debug=True)
