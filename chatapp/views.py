from django.shortcuts import render, redirect
from .forms import UserForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import date, timedelta
from .models import QuestionAnswer
import openai
import json
from openai import OpenAI


# Create your views here.
open_api_key = "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"
openai.api_key = open_api_key


@login_required(login_url='signin')
def index(request):
    today = date.today()
    yesterday = date.today() - timedelta(days=1)
    seven_days_ago = date.today() - timedelta(days=7)
    
    questions = QuestionAnswer.objects.filter(user=request.user)
    t_questions = questions.filter(created=today)
    y_questions = questions.filter(created=yesterday)
    s_questions = questions.filter(created__gte=seven_days_ago, created__lte=today)
    
    context = {"t_questions":t_questions, "y_questions": y_questions, "s_questions": s_questions}

    return render(request, "chatapp/index.html", context)


def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    form = UserForm()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            username = request.POST["username"]
            password = request.POST["password1"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("index")
    context = {"form": form}
    return render(request, "chatapp/signup.html", context)


def signin(request):
    err = None
    if request.user.is_authenticated:
        return redirect("index")
    
    if request.method == 'POST':
        
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")
        
        else:
            err = "Invalid Credentials"
        
        
    context = {"error": err}
    return render(request, "chatapp/signin.html", context)


def signout(request):
    logout(request)
    return redirect("signin")



def ask_openai(message):
    client = OpenAI(api_key=open_api_key)
    response = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a doctor. You will keep asking questions about your patient's symptoms and other details and reach to a final conclusion/diagnosis of what might be the problem for your patient. After you ask a handful of questions, you will give the patient a percentage probablity of different outcomes that may be the underlying result. If they say or ask anything that isnt related to health or medical discussions, then you will ignore it and steer the user back on topic."},
    {"role": "user", "content": message},
   
  ]
)
    
    response_message = response.choices[0].message.content
    return response_message


def getValue(request):
    data = json.loads(request.body)
    message = data["msg"] 
    response = ask_openai(message)
    QuestionAnswer.objects.create(user = request.user, question=message, answer=response)
    return JsonResponse({"msg": message, "res": response})