from flask import Flask, request, jsonify
import base64
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)

# Define the entities
entities = ["plant_name", "plant_disease", "disease_description", "water", "cure", "temperature", "sunlight"]

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Get the image from the request
        file = request.files['image']
        if file:
            # Convert the image to a base64 string
            image_data = file.read()
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # Construct the prompt in JSON format
            prompt = (
                "You are a highly knowledgeable AI assistant specializing in plant botany, plant classification, and disease detection. "
                "Your task is to classify the plant and detect the presence of disease in the provided image, extract detailed and informative content about the plant. "
                "Provide specific and relevant details based on visual analysis. If the exact name of the plant cannot be identified, suggest a closely related or similar plant name. Avoid using scientific names and focus on providing a common name and its class in the same field. Ensure that the response is in JSON format with key-value pairs, where each key corresponds to one of the entities listed below and the value provides detailed information.\n\n"
                "Entities to be described:\n\n"
                f"- **{entities[0]}**: Provide the common name of the plant along with its class or general classification (e.g., Mango (Stone fruit)). Only include this combined information in this field.\n"
                f"- **{entities[1]}**: Describe any visible disease symptoms on the plant, such as discoloration, spots, or deformities. Specify the most likely disease type without expressing uncertainty.\n"
                f"- **{entities[2]}**: Provide a comprehensive description of the disease. This should include details such as the common name, potential causes (e.g., fungal, bacterial, viral), symptoms, and any other relevant information.\n"
                f"- **{entities[3]}**: Based on visual inspection, estimate the water requirements for the plant. Note any indications like soil moisture, wilting, or other signs of hydration.\n"
                f"- **{entities[4]}**: Suggest potential cures or treatments for the plant's condition, if any. Include both organic and chemical options, preventive measures, and general care tips.\n"
                f"- **{entities[5]}**: Provide an estimation of the suitable temperature range for the plant. Infer from the plant's appearance or surrounding environment if exact data is unavailable.\n"
                f"- **{entities[6]}**: Assess the sunlight requirements for the plant, based on its condition and surroundings in the image. Specify whether full sun, partial shade, or full shade is ideal, along with any other observations.\n\n"
            )

            # Set the headers for the OpenAI API request
            gpt_headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }

            # Set the payload for the OpenAI API request
            gpt_payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ]
            }

            # Send the request to the OpenAI API
            gpt_response = requests.post("https://api.openai.com/v1/chat/completions", headers=gpt_headers, json=gpt_payload)
            response_data = gpt_response.json()

            # Extract the 'content' field from the response
            content = response_data['choices'][0]['message']['content']

            # Parse the JSON string in the 'content' field
            try:
                detailed_information = json.loads(content.replace('```json\n', '').replace('\n```', ''))

                # Check if the response indicates no plant found
                if not detailed_information or "no plant" in detailed_information.get("plant_name", "").lower():
                    raise ValueError("The image may not contain plant or upload again.")

                # Ensure plant_name is not "Unknown"
                if "Unknown" in detailed_information.get("plant_name", ""):
                    raise ValueError("The image may not contain plant or upload again.")

                # Truncate the disease_description to 30 words
                disease_description = detailed_information.get("disease_description", "")
                if isinstance(disease_description, str):
                    disease_description_words = disease_description.split()
                    if len(disease_description_words) > 30:
                        disease_description = " ".join(disease_description_words[:30]) + "..."
                    detailed_information["disease_description"] = disease_description

                # Extract titles and details
                titles = list(detailed_information.keys())
                details = list(detailed_information.values())

                # Extract values for plant_name, plant_disease, and disease_description
                plant_name = detailed_information.get("plant_name", "")
                plant_disease = detailed_information.get("plant_disease", "")
                disease_description = detailed_information.get("disease_description", "")

                # Filter out 'plant_name', 'plant_disease', and 'disease_description' from details
                filtered_details = [detail for title, detail in zip(titles, details)
                                    if title not in ["plant_name", "plant_disease", "disease_description"]]

                # Construct the response
                output = {
                    "plant_name": plant_name,
                    "plant_disease": plant_disease,
                    "disease_description": disease_description,
                    "Detailed_Information": {
                        "details": filtered_details,
                        "titles": [title for title in titles
                                   if title in ["water", "cure", "temperature", "sunlight"]]
                    }
                }

            except json.JSONDecodeError as e:
                return jsonify({"error": "The image may not contain plant or upload again."}), 500
            except ValueError as ve:
                return jsonify({"error": str(ve)}), 400

            return jsonify(output)
        else:
            return jsonify({"error": "No image provided"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
