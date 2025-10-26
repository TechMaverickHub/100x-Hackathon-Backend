from app.analytics.models import AIAnalytics


def save_ai_analytics(user, generation_type, content):

    ai_analytics = AIAnalytics(
        user=user,
        generation_type=generation_type,
        content=content
    )

    ai_analytics.save()

    return ai_analytics