from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import ExamRecord

scores_bp = Blueprint("scores", __name__, url_prefix="/api/scores")


@scores_bp.get("/stats")
def score_stats():
    student_name = request.args.get("studentName")
    subject = request.args.get("subject")
    query = db.session.query(
        ExamRecord.subject,
        db.func.count(ExamRecord.id).label("total"),
        db.func.avg(ExamRecord.score).label("avg_score"),
        db.func.max(ExamRecord.score).label("max_score"),
        db.func.sum(db.case((ExamRecord.passed == False, 1), else_=0)).label("fail_count"),
    ).group_by(ExamRecord.subject)
    if student_name:
        query = query.filter(ExamRecord.student_name.contains(student_name))
    if subject:
        query = query.filter_by(subject=subject)
    rows = query.all()
    result = []
    for row in rows:
        total = row.total or 0
        fail_count = row.fail_count or 0
        result.append({
            "subject": row.subject,
            "total": total,
            "avgScore": round(row.avg_score, 1) if row.avg_score else 0,
            "maxScore": row.max_score or 0,
            "failCount": fail_count,
            "passRate": round((total - fail_count) / total * 100, 1) if total else 0,
        })
    return jsonify(result)


@scores_bp.get("")
def list_scores():
    student_name = request.args.get("studentName")
    subject = request.args.get("subject")
    query = ExamRecord.query.order_by(ExamRecord.submitted_at.desc())
    if student_name:
        query = query.filter(ExamRecord.student_name.contains(student_name))
    if subject:
        query = query.filter_by(subject=subject)
    return jsonify([record.to_dict() for record in query.all()])
