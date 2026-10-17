from functools import lru_cache
from .embedding_service import embed

CATEGORY_EXAMPLES = {
    "Examination": ["exam registration form and examination dates", "semester exams, admit card, examination office", "test schedule, assessment, exam eligibility"],
    "Attendance": ["class attendance requirement and absence eligibility", "minimum attendance percentage and leave policy", "how many classes may I miss"],
    "Fees": ["tuition and semester fee payment", "accounts office, dues, fee deadline or receipt", "paying college charges online"],
    "Placements": ["campus recruitment and placement registration", "company eligibility criteria and job interviews", "placement cell and employer drives"],
    "Internship": ["internship approval, mentor, report and certificate", "industrial training during semester", "internship application guidelines"],
    "Timetable": ["class schedule, lecture time and room", "weekly timetable and class changes", "when and where are lectures"],
    "Academic": ["academic calendar, semester start and teaching weeks", "course curriculum, academic policy and assessments", "term dates and holidays"],
    "Admissions": ["admission eligibility, application and counselling", "applying to the college and required documents", "new student enrolment dates"],
    "Events": ["campus events, clubs and registration", "college festival schedule and venue", "student activity announcement"],
    "General": ["general campus help desk and student services", "where to ask a question about college services", "campus office directory and contact information"],
}

@lru_cache(maxsize=1)
def category_vectors():
    labels, examples = [], []
    for label, items in CATEGORY_EXAMPLES.items():
        for item in items: labels.append(label); examples.append(item)
    return labels, embed(examples)

def classify(query, query_vector=None):
    labels, vectors = category_vectors()
    q = query_vector if query_vector is not None else embed([query])
    scores = (vectors @ q[0]).tolist()
    best = max(range(len(scores)), key=scores.__getitem__)
    return {"category": labels[best], "category_confidence": round(max(0.0, float(scores[best])), 4)}
