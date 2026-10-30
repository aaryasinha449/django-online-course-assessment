from django.shortcuts import render, get_object_or_404, redirect
from .models import Course, Lesson, Question, Choice, Submission


def course_details(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    return render(request, "onlinecourse/course_details_bootstrap.html",
                  {"course": course})


def submit(request, lesson_id):
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    if request.method != "POST":
        return redirect("course_details", course_id=lesson.course_id)

    questions = lesson.questions.prefetch_related("choices").all()
    score = 0
    results = []

    for question in questions:
        selected_id = request.POST.get(str(question.id))
        selected = question.choices.filter(pk=selected_id).first() if selected_id else None
        correct = question.choices.filter(is_correct=True).first()
        is_correct = bool(selected and selected.is_correct)
        if is_correct:
            score += 1
        results.append({
            "question": question.text,
            "selected": selected.text if selected else "Not answered",
            "correct": correct.text if correct else "Not configured",
            "is_correct": is_correct,
        })

    submission = Submission.objects.create(
        user=request.user if request.user.is_authenticated else
             __import__("django.contrib.auth", fromlist=["get_user_model"]).get_user_model().objects.get(username="guest"),
        lesson=lesson,
        score=score,
    )
    request.session["exam_results"] = results
    request.session["exam_score"] = score
    request.session["exam_total"] = questions.count()
    return redirect("show_exam_result", submission_id=submission.id)


def show_exam_result(request, submission_id):
    submission = get_object_or_404(Submission, pk=submission_id)
    return render(request, "onlinecourse/exam_result.html", {
        "submission": submission,
        "results": request.session.get("exam_results", []),
        "total": request.session.get("exam_total", 0),
    })
