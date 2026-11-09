import speech_recognition as sr
import pyttsx3
import requests
import data as d
import time
import os
import webbrowser as ww
import pyautogui as p
import tkinter as tk


engine = pyttsx3.init()
recognizer = sr.Recognizer()

engine.say("Welcome master")
engine.runAndWait()

root=tk.Tk()
root.geometry("500x600")

def listen(src):
    
    try:
        recognizer.adjust_for_ambient_noise(src, duration=0.5)
        print("Listening...")
        audio = recognizer.listen(src, timeout=10, phrase_time_limit=7)
        text = recognizer.recognize_google(audio).lower()
        print(text)
        return text

    except sr.UnknownValueError:
        print("Couldn't understand. Listening again...")
        return   

    except sr.RequestError:
        print("Speech service unavailable.")
        engine.say("Sorry for inconvinent!,Data service is down.")
        engine.runAndWait()
        exit()

    except sr.WaitTimeoutError:
        print("Timeout! No speech detected.")
        return None

def typing_mode(src):
        engine.say("typing mode on")
        engine.runAndWait()
        newtext=listen(src)
        while True:
            if newtext: 
                if "stop typing mode" in newtext:            
                    engine.say("typing mode off")
                    engine.runAndWait()
                    break
                else:
                    if "press enter" in newtext:
                        p.press("Enter")           
                    elif "backspace" in newtext:
                        p.hotkey("ctrl","backspace")
                    elif "copy" in newtext:
                        p.click()
                        time.sleep(0.2)
                        p.hotkey("ctrl","c")
                        time.sleep(0.2)
                        engine.say("copied")
                        engine.runAndWait()
                    elif "copy all" in newtext:
                        p.hotkey("ctrl", "a")  
                        time.sleep(0.2)  
                        p.hotkey("ctrl", "c")  
                        time.sleep(0.2) 
                        engine.say("copied")
                        engine.runAndWait()
                    elif "paste" in newtext:
                        p.hotkey("ctrl", "v") 
                        engine.say("pasted")
                        engine.runAndWait()
                    else:
                        p.typewrite(newtext + " ")
                    newtext=listen(src)
            else:
                newtext=listen(src)
def joke():
        url = "https://official-joke-api.appspot.com/random_joke"
        response = requests.get(url)
        joke = response.json()
        print(f"{joke['setup']} - {joke['punchline']}")
        engine.say(joke["setup"])
        engine.runAndWait()
        time.sleep(1)
        engine.say(joke["punchline"])
        engine.runAndWait()

def code_win(key,code,line="list"):
                root.title(key)
                frame = tk.Frame(root)
                frame.pack(fill="both", expand=True, padx=10, pady=10)
                scrollbar = tk.Scrollbar(frame)
                scrollbar.pack(side="right", fill="y")
                text = tk.Text(frame, wrap="word", font=("Arial", 12), yscrollcommand=scrollbar.set)
                text.pack(fill="both", expand=True)
                text.insert("1.0", code)
                text.config(state="normal")
                scrollbar.config(command=text.yview)
                engine .say(f"here is code {line}")
                engine.runAndWait()
                root.after(5000,root.destroy)
                root.mainloop()

def option(src,text):
    print(f"in option: {text}")

    if "joke" in text:
        joke()

    elif "introduce" in text or "yourself" in text:
        engine.say(d.intro)
        engine.runAndWait()  

    elif "open" in text:

        for key, path in d.app.items():
            if key in text :
                os.system(path)
                engine.say(f"Opening {key}")
                engine.runAndWait()
                return

        for key, url in d.website.items():
            if key in text:
                ww.open(url)
                engine.say(f"Opening {key}")
                engine.runAndWait()
                return
            
    elif "search" in text:
        query=text.replace("search","")
        query1=query.split("on")[0]

        if "google" in text:      
            ww.open(f"https://www.google.com/search?q={query1}")
            
        
        elif "youtube" in text:
            ww.open(f"https://www.youtube.com/results?search_query={query1}")
        return   
    
    elif "vs " not in text and "code" in text :
        line=text.replace("for ","")
        line=line.split("code")
        if line[1] is None:
            engine.say("For what")
            engine.runAndWait()
            return
        if "list" in text:
            code_line=""
            for key,code in d.code.items():
                print(key)
                code_line = code_line + key + "\n"
            code_win("list of code",code_line)
        else:
            for key,code in d.code.items():
                if key in line[1]:
                    code_win(key,code,line[1])
                    break   
            else:
                    engine.say("sorry, i don't have that one")
                    engine.runAndWait()
                    return
            
    elif "typing mode" in text:
        typing_mode(src)
    
    elif "stop" in text:
        engine.say("I take your leave")
        engine.runAndWait()
        exit()

    else:
        engine.say("I didn't understand.")
        engine.runAndWait()
        return

def main():
   
    with sr.Microphone() as src: 
        while True:
            command = listen(src)
            if command is None:
                continue  

            elif "sky" in command:
                line=command.split("sky ")
                if "sky" in line[0]:
                    engine.say("Hello master")
                    engine.runAndWait()

                    while True:
                        text=listen(src)
                        if text is None:
                            continue

                        if "command mode" in text:
                            engine.say("command mode on")
                            engine.runAndWait()
                            while True:
                                text=listen(src)
                                if text is None:
                                    continue
                                if "stop typing" in text:
                                    break
                                else:
                                    option(src,text)
                        else:
                            option(src,text)
                            break
                else:
                    option(src,line[1])

            elif "stop" in command:
                engine.say("I take your leave")
                engine.runAndWait()
                break   

            else:
                engine.say("What?")
                engine.runAndWait()

main()
