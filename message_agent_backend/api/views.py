# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

# Create your views here.
from .query_gpt import query_gpt4, query_llm_assistant
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import MessageSerializer
import os
import re
import nltk
import uuid
import csv
import json

nltk.download('punkt')

def extract_text(ai_response_data):
    # Loop through the messages in the response data
    for message in ai_response_data.data:
        # Check if the role is 'assistant'
        if message.role == 'assistant':
            # Extract the content block
            for content_block in message.content:
                # Check if the content block type is 'text'
                if content_block.type == 'text':
                    # Extract the text value
                    return content_block.text.value
    return None

def classify_message_regex(message):
    patterns = {
        'appointment_scheduling': re.compile(r'\b(appointment|schedule|book)\b', re.IGNORECASE),
        'prescription_renewal': re.compile(r'\b(prescription|medication|tablets|medicine|refill|renew)\b', re.IGNORECASE),
        'lab_test_interpretation': re.compile(r'\b(lab|test|results|blood|interpret|understand)\b', re.IGNORECASE)
    }
    categories = set()
    latest_message = message[0] # Exstract latest message for classification
    sentences = nltk.sent_tokenize(latest_message) # Tokenise into sentences for seperate classification
    for sentence in sentences:
        for category, pattern in patterns.items():
            if pattern.search(sentence):
                categories.add(category)
    if not categories:
        categories.add('unknown')
    return list(categories)

def classify_message_llm(message):
    categories = set()
    latest_message = message[0] # Exstract latest message for classification
    sentences = nltk.sent_tokenize(latest_message) # Tokenise into sentences for seperate classification
    for sentence in sentences:
        print('sentence:', sentence)
        completion = query_llm_assistant(sentence, assistant_id='asst_zgkMJ5Fe5ODGyHQWWcsVKBkB')
        response_text = extract_text(completion)
        print('response_text:', response_text)
        categories.add(response_text)
    if not categories:
        categories.add('unknown')
    print('categories:', categories)
    return list(categories)

def draft_response(patient, message, message_categories):
    input_text = f'Name: {patient}\nMessage: {message}\nCategories: {message_categories}'
    completion = query_llm_assistant(input_text, assistant_id='asst_PziJ9XgAcegPOOKQPNboEIMc')
    response_text = extract_text(completion)
    return response_text

class MessageView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            # Frist use regex
            message_categories = classify_message_regex(serializer.validated_data['message'])
            #message_categories = ['unknown'] # To test llm method

            # If all unknown pass to llm 
            # Note this may need to change in the future to assign each sentence with a type so some dont get missed
            if all(item == 'unknown' for item in message_categories): # If all unknown pass to llm
                print("\nUsing classify_message_llm!\n")
                message_categories = classify_message_llm(serializer.validated_data['message'])
                categories_method = 'llm'
            else:
                categories_method = 'regex'

            # Remove 'unknown' from the categories
            message_categories = [item for item in message_categories if item != 'unknown']
            
            # Check if there are any non-'unknown' categories and if so get draft response
            if message_categories:
                print('message_categories:', message_categories)
                print("\nUsing draft_response!\n")
                example_response = draft_response(serializer.validated_data['patient'], serializer.validated_data['message'], message_categories)
            else:
                message_categories = ['unknown'] # Set to only one unknown
                example_response = "Not available"

            job_id = str(uuid.uuid4())  # Generate a unique job ID

            response_data = {
                'jobId' : job_id,
                'requestType': message_categories,
                'typeMethod': categories_method,
                'exampleResponse':example_response ,
            }

            # Save
            save_json_to_csv(request.data, response_data)

            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
def save_json_to_csv(input_json, output_json, filename='example_data.csv'):
    file_exists = os.path.isfile(filename)

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['input', 'output'])  # Write header if file does not exist
        
        input_str = json.dumps(input_json)
        output_str = json.dumps(output_json)
        writer.writerow([input_str, output_str])


# Add in action words like get or call or speak or contanct that should lead to an appointment  !!!