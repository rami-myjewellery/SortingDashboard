# app/utils.py
from typing import List, Optional
from app.models import Person

def get_or_create_person(people: List[Person], name: str,category : str , comment:str) -> Person:
    for p in people:
        if p.name == name:
            return p

    # — new operator —
    new_person = Person(name=name,category=category,comment=comment, speed=0, idleSeconds=0)
    people.append(new_person)
    return new_person