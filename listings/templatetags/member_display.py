from django import template

register = template.Library()


def _mask_email(email: str) -> str:
    if not email or '@' not in email:
        return email
    local, domain = email.split('@', 1)
    if len(local) <= 2:
        masked_local = local[0] + "***" if local else "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    # Optionally mask domain part before TLD
    domain_parts = domain.split('.')
    if len(domain_parts) > 1 and len(domain_parts[0]) > 2:
        domain_parts[0] = domain_parts[0][0] + "***" + domain_parts[0][-1]
    masked_domain = '.'.join(domain_parts)
    return f"{masked_local}@{masked_domain}"


@register.filter(name='masked_email')
def masked_email(value):
    """Mask an email address for display."""
    return _mask_email(value)


@register.filter(name='member_display_name')
def member_display_name(user):
    """
    Return a member's display name based on available personal profile names.
    Preference order:
    - If PersonalProfile has any of first_name, surname, last_name: use up to two available in order
      (first two of [first_name, surname, last_name])
    - Else if user model has first_name/last_name: use available ones (up to two)
    - Else: return masked email
    """
    if not user:
        return ''

    # Gather candidate names from PersonalProfile if available
    names = []
    # Correct reverse relation name is 'profile' (users.PersonalProfile.related_name)
    profile = getattr(user, 'profile', None)
    if profile:
        for part in [getattr(profile, 'first_name', None), getattr(profile, 'surname', None), getattr(profile, 'last_name', None)]:
            if part:
                names.append(str(part).strip())
    # Use first two distinct non-empty parts from PersonalProfile only
    names = [n for n in names if n]
    if names:
        unique = []
        for n in names:
            if n not in unique:
                unique.append(n)
        display = ' '.join(unique[:2])
        return display

    # If no PersonalProfile or no names, fallback to masked email
    email = getattr(user, 'email', '')
    return _mask_email(email)


