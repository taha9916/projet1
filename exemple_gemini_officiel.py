# Exemple d'utilisation de l'API Gemini avec la bibliothèque officielle google-generativeai

import os
import sys
import argparse
import pathlib
import google.generativeai as genai
from PIL import Image

def configure_genai(api_key):
    """Configure l'API Gemini avec la clé API fournie."""
    genai.configure(api_key=api_key)

def list_models():
    """Liste les modèles disponibles."""
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")

def generate_text(prompt, model_name="gemini-2.0-flash"):
    """Génère du texte avec l'API Gemini."""
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text

def analyze_image(image_path, prompt, model_name="gemini-2.0-pro-vision"):
    """Analyse une image avec l'API Gemini."""
    model = genai.GenerativeModel(model_name)
    
    # Charger l'image
    img = Image.open(image_path)
    
    # Générer une réponse basée sur l'image et le prompt
    response = model.generate_content([prompt, img])
    return response.text
def main():
    parser = argparse.ArgumentParser(description="Exemple d'utilisation de l'API Gemini avec google-generativeai")
    parser.add_argument("--api_key", help="Clé API Gemini")
    parser.add_argument("--image", help="Chemin vers l'image à analyser")
    parser.add_argument("--prompt", default="Explain how AI works in a few words", help="Prompt à envoyer à l'API")
    parser.add_argument("--mode", choices=["text", "image", "list_models"], default="text", 
                        help="Mode d'utilisation (texte, image ou liste des modèles)")
    parser.add_argument("--model", help="Nom du modèle à utiliser (par défaut: gemini-2.0-flash pour le texte, gemini-2.0-pro-vision pour l'image)")
    
    args = parser.parse_args()
    
    # Vérifier si la clé API est fournie
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Erreur: Veuillez fournir une clé API Gemini via --api_key ou la variable d'environnement GEMINI_API_KEY")
        sys.exit(1)
    
    # Configurer l'API
    configure_genai(api_key)
    
    if args.mode == "list_models":
        print("Modèles Gemini disponibles:")
        list_models()
    elif args.mode == "text":
        # Générer du texte
        model_name = args.model or "gemini-2.0-flash"
        print(f"\nUtilisation du modèle: {model_name}")
        print(f"Prompt: {args.prompt}")
        
        try:
            response = generate_text(args.prompt, model_name)
            print("\nRéponse de Gemini:")
            print(response)
        except Exception as e:
            print(f"Erreur lors de la génération de texte: {e}")
    else:
        # Analyser une image
        if not args.image:
            print("Erreur: Veuillez fournir une image via --image")
            sys.exit(1)
            
        image_path = pathlib.Path(args.image)
        
        model_name = args.model or "gemini-2.0-pro-vision"
        print(f"\nUtilisation du modèle: {model_name}")
        print(f"Image: {args.image}")
        print(f"Prompt: {args.prompt}")
        
        try:
            response = analyze_image(args.image, args.prompt, model_name)
            print("\nRéponse de Gemini:")
            print(response)
        except Exception as e:
            print(f"Erreur lors de l'analyse de l'image: {e}")

if __name__ == "__main__":
    main()