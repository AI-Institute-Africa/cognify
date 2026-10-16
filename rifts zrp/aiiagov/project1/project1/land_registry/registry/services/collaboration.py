import re
from django.contrib.auth.models import User
from django.utils import timezone
from ..models import ProjectComment, CommentEditHistory, ProjectAlert

class CollaborationService:
    @staticmethod
    def parse_mentions(comment):
        """
        Extracts @usernames from comment content and links them to the comment.
        """
        mention_pattern = r'@(\w+)'
        usernames = re.findall(mention_pattern, comment.content)
        
        for username in usernames:
            user = User.objects.filter(username=username).first()
            if user:
                comment.mentioned_users.add(user)
                CollaborationService.notify_mention(comment, user)

    @staticmethod
    def notify_mention(comment, user):
        """
        Creates a ProjectAlert for the mentioned user.
        """
        context_name = "Project"
        obj = comment.project
        if comment.task:
            context_name = f"Task '{comment.task.title}'"
            obj = comment.task.phase.project
        elif comment.sprint:
            context_name = f"Sprint '{comment.sprint.name}'"
            obj = comment.sprint.phase.project
        elif comment.phase:
            context_name = f"Phase '{comment.phase.name}'"
            obj = comment.phase.project

        ProjectAlert.objects.create(
            project=obj,
            task=comment.task,
            phase=comment.phase,
            sprint=comment.sprint,
            recipient=user,
            alert_type='Predictive', # Using Predictive as a fallback or could add 'Mention'
            message=f"Interaction Alert: {comment.author.username} mentioned you on {context_name}: \"{comment.content[:50]}...\""
        )

    @staticmethod
    def record_edit(comment, old_content, editor):
        """
        Records the previous content in the edit history for institutional audit trail.
        """
        CommentEditHistory.objects.create(
            comment=comment,
            content_before=old_content,
            edited_by=editor
        )
