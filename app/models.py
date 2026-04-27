import uuid
from datetime import datetime, timezone

from app import db


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_uuid() -> str:
    return str(uuid.uuid4())


MEDIA_TYPES = ("book", "film", "tv", "game", "album")
ENTRY_STATUSES = ("backlog", "in_progress", "completed", "abandoned", "dropped")


entry_tags = db.Table(
    "entry_tags",
    db.Column(
        "entry_id",
        db.Integer,
        db.ForeignKey("entries.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "tag_id",
        db.Integer,
        db.ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class MediaItem(db.Model):
    __tablename__ = "media_items"

    id = db.Column(db.String(36), primary_key=True, default=_new_uuid)
    type = db.Column(db.String(16), nullable=False, index=True)
    title = db.Column(db.Text, nullable=False, index=True)
    creators = db.Column(db.JSON, nullable=False, default=list)
    release_year = db.Column(db.Integer)
    cover_url = db.Column(db.Text)
    provider = db.Column(db.String(32), nullable=False)
    external_id = db.Column(db.String(128), nullable=False)
    # `metadata` is reserved on SQLAlchemy's declarative base, hence the rename.
    item_metadata = db.Column("metadata", db.JSON, nullable=False, default=dict)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)

    entries = db.relationship(
        "Entry", back_populates="media", cascade="all, delete-orphan"
    )

    __table_args__ = (
        db.CheckConstraint(
            f"type IN ({','.join(repr(t) for t in MEDIA_TYPES)})",
            name="ck_media_type",
        ),
        db.UniqueConstraint("provider", "external_id", name="uq_media_provider_extid"),
    )


class Entry(db.Model):
    __tablename__ = "entries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    media_id = db.Column(
        db.String(36),
        db.ForeignKey("media_items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    profile_id = db.Column(db.String(100), nullable=False, index=True)
    status = db.Column(db.String(16), nullable=False, index=True)
    rating = db.Column(db.Integer)
    started_at = db.Column(db.DateTime)
    finished_at = db.Column(db.DateTime)
    notes = db.Column(db.Text, nullable=False, default="")
    iteration = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, nullable=False, default=_utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=_utcnow, onupdate=_utcnow
    )

    media = db.relationship("MediaItem", back_populates="entries")
    tags = db.relationship("Tag", secondary=entry_tags, back_populates="entries")

    __table_args__ = (
        db.CheckConstraint(
            f"status IN ({','.join(repr(s) for s in ENTRY_STATUSES)})",
            name="ck_entry_status",
        ),
        db.CheckConstraint(
            "rating IS NULL OR (rating BETWEEN 1 AND 10)",
            name="ck_entry_rating",
        ),
    )


class Tag(db.Model):
    __tablename__ = "tags"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

    entries = db.relationship("Entry", secondary=entry_tags, back_populates="tags")
