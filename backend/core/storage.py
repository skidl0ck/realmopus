from django.conf import settings


def get_public_media_storage():
    """Storage for content that's meant to be permanently, publicly visible --
    lot photos, blog images, testimonial photos, project cover images, floor
    plans, and the site's own logo. Deliberately separate from the app's
    default storage (see config/settings.py), which is private with
    presigned, expiring URLs -- correct for contracts, receipts, and expense
    documents, but wrong for public marketing content: an expiring URL on a
    lot photo means the image silently breaks an hour after the page was
    generated, for anyone who cached the page or has it indexed by a search
    engine.

    A callable rather than a plain instance so it's evaluated lazily, at the
    point a field actually needs it -- not at import time, when
    settings.AWS_STORAGE_BUCKET_NAME may not be configured yet (e.g. local
    dev, or Django management commands run before .env is loaded). This
    mirrors the same "only when S3 is actually configured" gating the
    default storage already uses.
    """
    if getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
        from storages.backends.s3 import S3Storage
        # default_acl explicitly set to None, not just omitted -- AWS
        # requires an S3 PUT request to either specify the
        # bucket-owner-full-control canned ACL or send no ACL at all when
        # Object Ownership is "ACLs disabled"; anything else (including
        # django-storages' own internal default) gets rejected outright
        # with AccessControlListNotSupported. Public access for these
        # prefixes comes from a bucket policy instead (see
        # docs/DEPLOYMENT.md) -- querystring_auth=False is what actually
        # matters here, since that's what stops these URLs from expiring.
        return S3Storage(querystring_auth=False, default_acl=None)
    from django.core.files.storage import default_storage
    return default_storage