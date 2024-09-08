
from flask import Flask, render_template, request, session
import vertexai
from vertexai.language_models import TextGenerationModel, GroundingSource, ChatModel, ChatMessage
from google.oauth2 import service_account
import urllib.parse
import os



private_key = os.environ.get('GCP_PRIVATE_KEY')
project_id = os.environ.get('GCP_PROJECT_ID')
service_email = os.environ.get('GCP_SERVICE_ACCOUNT_EMAIL')
private_key_id = os.environ.get('PRIVATE_KEY_ID')
client_id = os.environ.get('CLIENT_ID')
session_password = os.environ.get('SESSION_PWD')
data_store_id = os.environ.get('DATA_STORE_ID')
project_name = os.environ.get('PROJECT_NAME')

credentials = service_account.Credentials.from_service_account_info({
    "type": "service_account",
    "project_id": project_id,
    "private_key_id": private_key_id,
    "private_key": private_key,
    "client_email": service_email,
    "client_id": client_id,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/brite-app-service%40project-steinn.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"


})

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY')


import json
from google.oauth2 import service_account


vertexai.init(project="project-steinn", credentials=credentials)
chat_model = ChatModel.from_pretrained("chat-bison")
parameters = {
    "candidate_count": 1,
    "max_output_tokens": 1024,
    "temperature": 0.2,
    "top_p": 1
}


grounding_source = GroundingSource.VertexAISearch(data_store_id=data_store_id, location="global", project=project_name)
message_log = [ChatMessage( content='Hey', author='user'), ChatMessage(content='Hello, I am an AI', author='bot')]
conversation_history = []  


@app.route("/")
def home():
    if 'logged_in' in session and session['logged_in']:
        global conversation_history, message_log
        conversation_history = []
        message_log = [ChatMessage(content='Hey', author='user'), ChatMessage(content='Hello, I am an AI', author='bot')]
        
        return render_template('chat.html')
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    password = request.form['password']
    if password == session_password:
        session['logged_in'] = True
        global conversation_history, message_log
        conversation_history = []
        message_log = [ChatMessage(content='Hey', author='user'), ChatMessage(content='Hello, I am an AI', author='bot')]
        return render_template('chat.html', history=conversation_history)

# Define route for processing form submission
@app.route('/chat', methods=['POST', 'GET'])
def process_form():
    chat = chat_model.start_chat(
        context="""Background: You are human replica. based on context containing opinions, answer the questions.""",
        message_history = message_log
    )

    user_question = session.get('question')
    conversation_history.append(('User', user_question))
    response = chat.send_message(user_question, **parameters, grounding_source=grounding_source)
    conversation_history.append(('Model', response.text))
    print(f"""-----------------------------------------------
            {message_log}
            -----------------------------------------------------""")
    
    return render_template('chat.html', history=conversation_history)


@app.route('/load', methods=['POST'])
def show_chat():
    session['question'] = request.form['question']
    return render_template("loading.html", history=conversation_history)

    
@app.route('/new')
def reset():
    global conversation_history, message_log
    conversation_history = []
    message_log = [ChatMessage(content='Hey', author='user'), ChatMessage(content='Hello, I am an AI', author='bot')]
    return render_template('chat.html', history=conversation_history)

@app.route('/error')
def error():
    return render_template('error.html')


