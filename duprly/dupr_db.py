"""
    Relational representation of DUPR Data
"""
from datetime import date, datetime
from typing import List, Optional
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy import String, ForeignKey, Integer, Float, DateTime, Text, Boolean, UniqueConstraint
from sqlalchemy import Table, Column, select
from sqlalchemy.orm import Session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column, relationship


engine = None


def ensure_rating_player_cache(db_engine) -> None:
    """
    Ensure rating table has denormalized player columns for easier browsing in tools
    like Datasette, and backfill missing values from player table.
    """
    with db_engine.begin() as conn:
        table_info = conn.exec_driver_sql("PRAGMA table_info(rating)").fetchall()
        columns = {row[1] for row in table_info}

        if "player_dupr_id" not in columns:
            conn.exec_driver_sql("ALTER TABLE rating ADD COLUMN player_dupr_id INTEGER")
        if "player_full_name" not in columns:
            conn.exec_driver_sql("ALTER TABLE rating ADD COLUMN player_full_name VARCHAR(128)")

        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_rating_player_dupr_id ON rating(player_dupr_id)"
        )
        conn.exec_driver_sql(
            """
            UPDATE rating
               SET player_dupr_id = (
                       SELECT p.dupr_id
                         FROM player p
                        WHERE p.id = rating.player_id
                   ),
                   player_full_name = (
                       SELECT p.full_name
                         FROM player p
                        WHERE p.id = rating.player_id
                   )
             WHERE player_id IS NOT NULL
               AND (player_dupr_id IS NULL OR player_full_name IS NULL)
            """
        )


def ensure_datasette_views(db_engine) -> None:
    """
    Create deterministic analytics views used by Datasette dashboards/canned queries.
    """
    drop_order = [
        "v_club_top_risers_90d",
        "v_club_rating_snapshot",
        "v_club_directory",
        "v_player_opponent_stats",
        "v_player_partner_stats",
        "v_player_match_results",
        "v_player_rating_summary_90d",
        "v_player_rating_points",
        "v_player_current_rating",
        "v_player_directory",
    ]

    create_statements = [
        """
        CREATE VIEW v_player_directory AS
        SELECT
            p.dupr_id AS player_dupr_id,
            COALESCE(NULLIF(TRIM(p.full_name), ''), 'Unknown') AS player_full_name,
            p.club_id,
            printf(
                '%s [%d]',
                COALESCE(NULLIF(TRIM(p.full_name), ''), 'Unknown'),
                p.dupr_id
            ) AS player_label
        FROM player p
        WHERE p.dupr_id IS NOT NULL
        """,
        """
        CREATE VIEW v_club_directory AS
        WITH candidates AS (
            SELECT
                p.club_id AS club_id,
                NULL AS club_name
            FROM player p
            WHERE p.club_id IS NOT NULL
              AND p.club_id != 0
            UNION ALL
            SELECT
                CAST(
                    CASE
                        WHEN json_valid(pms.player_metadata_json)
                        THEN json_extract(pms.player_metadata_json, '$.clubId')
                        ELSE NULL
                    END
                    AS INTEGER
                ) AS club_id,
                NULLIF(
                    TRIM(
                        CAST(
                            CASE
                                WHEN json_valid(pms.player_metadata_json)
                                THEN json_extract(pms.player_metadata_json, '$.clubName')
                                ELSE NULL
                            END
                            AS TEXT
                        )
                    ),
                    ''
                ) AS club_name
            FROM player_metadata_snapshot pms
            WHERE json_valid(pms.player_metadata_json)
              AND json_extract(pms.player_metadata_json, '$.clubId') IS NOT NULL
            UNION ALL
            SELECT
                CAST(
                    CASE
                        WHEN json_valid(pmr.match_json)
                        THEN json_extract(pmr.match_json, '$.clubId')
                        ELSE NULL
                    END
                    AS INTEGER
                ) AS club_id,
                NULLIF(
                    TRIM(
                        CAST(
                            CASE
                                WHEN json_valid(pmr.match_json)
                                THEN json_extract(pmr.match_json, '$.clubName')
                                ELSE NULL
                            END
                            AS TEXT
                        )
                    ),
                    ''
                ) AS club_name
            FROM player_match_raw pmr
            WHERE json_valid(pmr.match_json)
              AND json_extract(pmr.match_json, '$.clubId') IS NOT NULL
        )
        SELECT
            c.club_id,
            COALESCE(MAX(c.club_name), 'Club ' || c.club_id) AS club_name,
            printf(
                '%s [%d]',
                COALESCE(MAX(c.club_name), 'Club ' || c.club_id),
                c.club_id
            ) AS club_label
        FROM candidates c
        WHERE c.club_id IS NOT NULL
          AND c.club_id != 0
        GROUP BY c.club_id
        """,
        """
        CREATE VIEW v_player_current_rating AS
        SELECT
            r.id AS rating_id,
            r.player_id,
            COALESCE(r.player_dupr_id, p.dupr_id) AS player_dupr_id,
            COALESCE(r.player_full_name, p.full_name) AS player_full_name,
            p.club_id,
            r.singles,
            r.singles_verified,
            r.is_singles_provisional,
            r.doubles,
            r.doubles_verified,
            r.is_doubles_provisional
        FROM rating r
        LEFT JOIN player p ON p.id = r.player_id
        """,
        """
        CREATE VIEW v_player_rating_points AS
        SELECT
            prh.id AS rating_history_id,
            prh.player_dupr_id,
            COALESCE(p.full_name, 'Unknown') AS player_full_name,
            p.club_id,
            prh.rating_type,
            prh.rating_date,
            prh.match_date,
            prh.rating,
            prh.changed_by_admin,
            prh.scope_start_date,
            prh.scope_end_date,
            prh.row_index,
            prh.fetched_at
        FROM player_rating_history prh
        LEFT JOIN player p ON p.dupr_id = prh.player_dupr_id
        """,
        """
        CREATE VIEW v_player_rating_summary_90d AS
        WITH recent AS (
            SELECT
                vrp.*,
                ROW_NUMBER() OVER (
                    PARTITION BY vrp.player_dupr_id, vrp.rating_type
                    ORDER BY vrp.rating_date ASC, vrp.row_index ASC, vrp.rating_history_id ASC
                ) AS rn_first,
                ROW_NUMBER() OVER (
                    PARTITION BY vrp.player_dupr_id, vrp.rating_type
                    ORDER BY vrp.rating_date DESC, vrp.row_index DESC, vrp.rating_history_id DESC
                ) AS rn_last
            FROM v_player_rating_points vrp
            WHERE vrp.rating_date >= date('now', '-90 day')
        )
        SELECT
            player_dupr_id,
            player_full_name,
            club_id,
            rating_type,
            COUNT(*) AS points_90d,
            MAX(CASE WHEN rn_first = 1 THEN rating END) AS first_rating_90d,
            MAX(CASE WHEN rn_last = 1 THEN rating END) AS latest_rating_90d,
            (
                MAX(CASE WHEN rn_last = 1 THEN rating END) -
                MAX(CASE WHEN rn_first = 1 THEN rating END)
            ) AS delta_rating_90d,
            MIN(rating_date) AS first_rating_date_90d,
            MAX(rating_date) AS latest_rating_date_90d
        FROM recent
        GROUP BY player_dupr_id, player_full_name, club_id, rating_type
        """,
        """
        CREATE VIEW v_player_match_results AS
        SELECT
            m.id AS match_db_id,
            m.match_id,
            m.date AS match_date,
            m.name AS event_name,
            m.match_source,
            m.match_type,
            t.id AS team_id,
            t.is_winner,
            CASE WHEN t.is_winner THEN 'W' ELSE 'L' END AS result,
            p.id AS player_id,
            p.dupr_id AS player_dupr_id,
            p.full_name AS player_full_name,
            p.club_id
        FROM "match" m
        JOIN match_team t ON t.match_id = m.id
        JOIN match_team_player mtp ON mtp.match_team_id = t.id
        JOIN player p ON p.id = mtp.player_id
        """,
        """
        CREATE VIEW v_player_partner_stats AS
        WITH partner_rows AS (
            SELECT
                pmr.match_id,
                pmr.match_date,
                pmr.player_dupr_id,
                pmr.player_full_name,
                pmr.club_id,
                pmr.is_winner,
                partner.dupr_id AS partner_dupr_id,
                partner.full_name AS partner_full_name
            FROM v_player_match_results pmr
            JOIN match_team_player mtp_partner
              ON mtp_partner.match_team_id = pmr.team_id
             AND mtp_partner.player_id != pmr.player_id
            JOIN player partner ON partner.id = mtp_partner.player_id
        )
        SELECT
            player_dupr_id,
            player_full_name,
            club_id,
            partner_dupr_id,
            partner_full_name,
            COUNT(DISTINCT match_id) AS matches_played,
            SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
            ROUND(
                1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                NULLIF(COUNT(DISTINCT match_id), 0),
                4
            ) AS win_rate,
            MAX(match_date) AS last_match_date
        FROM partner_rows
        GROUP BY
            player_dupr_id,
            player_full_name,
            club_id,
            partner_dupr_id,
            partner_full_name
        """,
        """
        CREATE VIEW v_player_opponent_stats AS
        WITH opponent_rows AS (
            SELECT
                pmr.match_id,
                pmr.match_date,
                pmr.player_dupr_id,
                pmr.player_full_name,
                pmr.club_id,
                pmr.is_winner,
                opp.player_dupr_id AS opponent_dupr_id,
                opp.player_full_name AS opponent_full_name
            FROM v_player_match_results pmr
            JOIN v_player_match_results opp
              ON opp.match_db_id = pmr.match_db_id
             AND opp.team_id != pmr.team_id
        )
        SELECT
            player_dupr_id,
            player_full_name,
            club_id,
            opponent_dupr_id,
            opponent_full_name,
            COUNT(DISTINCT match_id) AS matches_played,
            SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
            ROUND(
                1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                NULLIF(COUNT(DISTINCT match_id), 0),
                4
            ) AS win_rate,
            MAX(match_date) AS last_match_date
        FROM opponent_rows
        GROUP BY
            player_dupr_id,
            player_full_name,
            club_id,
            opponent_dupr_id,
            opponent_full_name
        """,
        """
        CREATE VIEW v_club_rating_snapshot AS
        WITH base AS (
            SELECT
                p.club_id,
                COUNT(*) AS players,
                SUM(CASE WHEN r.doubles IS NOT NULL THEN 1 ELSE 0 END) AS doubles_players,
                ROUND(AVG(r.doubles), 4) AS avg_doubles_rating,
                SUM(CASE WHEN r.singles IS NOT NULL THEN 1 ELSE 0 END) AS singles_players,
                ROUND(AVG(r.singles), 4) AS avg_singles_rating,
                SUM(CASE WHEN r.is_doubles_provisional THEN 1 ELSE 0 END) AS doubles_provisional_players,
                SUM(CASE WHEN r.is_singles_provisional THEN 1 ELSE 0 END) AS singles_provisional_players
            FROM player p
            LEFT JOIN rating r ON r.player_id = p.id
            GROUP BY p.club_id
        )
        SELECT
            b.club_id,
            COALESCE(cd.club_name, 'Club ' || b.club_id) AS club_name,
            b.players,
            b.doubles_players,
            b.avg_doubles_rating,
            b.singles_players,
            b.avg_singles_rating,
            b.doubles_provisional_players,
            b.singles_provisional_players
        FROM base b
        LEFT JOIN v_club_directory cd ON cd.club_id = b.club_id
        """,
        """
        CREATE VIEW v_club_top_risers_90d AS
        SELECT
            v.club_id,
            COALESCE(cd.club_name, 'Club ' || v.club_id) AS club_name,
            v.player_dupr_id,
            v.player_full_name,
            v.rating_type,
            v.points_90d,
            v.first_rating_90d,
            v.latest_rating_90d,
            v.delta_rating_90d,
            v.first_rating_date_90d,
            v.latest_rating_date_90d
        FROM v_player_rating_summary_90d v
        LEFT JOIN v_club_directory cd ON cd.club_id = v.club_id
        WHERE v.points_90d >= 2
        """,
    ]

    with db_engine.begin() as conn:
        for view_name in drop_order:
            conn.exec_driver_sql(f"DROP VIEW IF EXISTS {view_name}")
        for statement in create_statements:
            conn.exec_driver_sql(statement)


def open_db():
    global engine
    # engine = create_engine("sqlite+pysqlite:///:memory:", echo=False)
    engine = create_engine("sqlite+pysqlite:///dupr.sqlite", echo=False,  connect_args={'timeout': 15})
    Base.metadata.create_all(engine)
    ensure_rating_player_cache(engine)
    ensure_datasette_views(engine)
    return engine


class Base(DeclarativeBase):
    pass


def _fix_rating_json(data: dict) -> dict:
    # This is a very much a KLUDGE because the api
    # returns ratings in two different ways depending
    # on the player get call or the club member call
    if data.get("ratings"):
        r = data.pop("ratings")
        for (k, v) in r.items():
            data[k] = v
    return data


def _cv_rating_json(s: str):
    # deal with NR vs 3.45
    if s is None:
        return None
    if s == "NR":
        return None
    return float(s)


class Rating(Base):
    __tablename__ = "rating"

    id: Mapped[int] = mapped_column(primary_key=True)
    doubles: Mapped[Optional[float]] = mapped_column(Float)
    doubles_verified: Mapped[Optional[float]] = mapped_column(Float)
    is_doubles_provisional: Mapped[bool] = mapped_column(default=True)

    singles: Mapped[Optional[float]] = mapped_column(Float)
    singles_verified: Mapped[Optional[float]] = mapped_column(Float)
    is_singles_provisional: Mapped[bool] = mapped_column(default=True)

    player_dupr_id: Mapped[Optional[int]] = mapped_column(Integer)
    player_full_name: Mapped[Optional[str]] = mapped_column(String(128))

    player_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    player: Mapped["Player"] = relationship(back_populates="rating")

    @staticmethod
    def str_rating(s, s_verified, is_provisional):
        if is_provisional:
            v = f"{s}*" if s else "NR"
            return v
        else:
            v = f"{s_verified}" if s_verified else s  # "NR"
            return v

    def singles_rating(self):
        return Rating.str_rating(
            self.singles, self.singles_verified,
            self.is_singles_provisional)

    def doubles_rating(self):
        return Rating.str_rating(
            self.doubles, self.doubles_verified,
            self.is_doubles_provisional)

    def __repr__(self) -> str:
        return f"{self.doubles_rating()} / {self.singles_rating()}"


class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(primary_key=True)
    dupr_id: Mapped[int] = mapped_column(Integer)
    full_name: Mapped[str] = mapped_column(String(128))
    first_name: Mapped[Optional[str]] = mapped_column(String(128))
    last_name: Mapped[Optional[str]] = mapped_column(String(128))
    gender: Mapped[Optional[str]] = mapped_column()
    age: Mapped[Optional[int]] = mapped_column()
    image_url: Mapped[Optional[str]] = mapped_column(String(256))
    email: Mapped[Optional[str]] = mapped_column(String(256))
    phone: Mapped[Optional[str]] = mapped_column(String(64))
    club_id: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Note: in 1-1 mapping, no need to use the uselist=false
    # param if we are using Mapped annotation
    rating: Mapped["Rating"] = relationship(back_populates="player")

    match_teams: Mapped[List["MatchTeam"]] = relationship(
        secondary="match_team_player"
    )

    def __repr__(self) -> str:
        return f"Player {self.full_name} {self.rating}"

    @classmethod
    def get(cls, sess: Session, dupr_id: int) -> "Player":
        """ Get player by id, or none
        """
        p = sess.execute(select(Player).where(
            Player.dupr_id == dupr_id)).scalar_one_or_none()
        return p

    @classmethod
    def save(this, sess: Session, player: "Player") -> "Player":
        """ Insert or update this player
            Deal with child objects
        """
        p = Player.get(sess, player.dupr_id)
        if p:
            # update, carefully
            p.full_name = player.full_name
            p.first_name = player.first_name
            p.last_name = player.last_name
            p.gender = player.gender
            p.age = player.age
            p.image_url = player.image_url
            p.email = player.email
            p.phone = player.phone

            p.rating.doubles = player.rating.doubles if player.rating.doubles else None
            p.rating.doubles_verified = player.rating.doubles_verified if player.rating.doubles_verified else None
            p.rating.is_doubles_provisional = player.rating.is_doubles_provisional

            p.rating.singles = player.rating.singles if player.rating.singles else None
            p.rating.singles_verified = player.rating.singles_verified if player.rating.singles_verified else None
            p.rating.is_singles_provisional = player.rating.is_singles_provisional
            p.rating.player_dupr_id = p.dupr_id
            p.rating.player_full_name = p.full_name
            p.club_id = player.club_id if player.club_id else 0
            sess.add(p)
            return p
        else:
            if player.rating:
                player.rating.player_dupr_id = player.dupr_id
                player.rating.player_full_name = player.full_name
            sess.add(player)
            return player

    @classmethod
    def from_json(cls, d: dict) -> 'Player':
        try:
            p = Player()
            # this can be duprId or id
            p.dupr_id = d.get("duprId")
            if not p.dupr_id:
                p.dupr_id = d.get("id")
            # There seems to a API bug where player in matches
            # return a different DuprID in the form of NNNANNN where as
            # other IDs are just numeric. So stick to id field
            p.dupr_id = d.get("id")
            p.full_name = d.get("fullName")
            p.image_url = d.get("imageUrl")

            p.email = d.get("email")
            p.gender = d.get("gender")
            p.age = d.get("age")
            p.club_id = d.get("club_id")

            p.rating = Rating()

            _fix_rating_json(d)
            p.rating.singles = _cv_rating_json(d.get("singles"))
            p.rating.singles_verified = _cv_rating_json(d.get("singlesVerified"))
            p.rating.is_singles_provisional = d.get("singlesProvisional")

            p.rating.doubles = _cv_rating_json(d.get("doubles"))
            p.rating.doubles_verified = _cv_rating_json(d.get("doublesVerified"))
            p.rating.is_doubles_provisional = d.get("doublesProvisional")
            p.rating.player_dupr_id = p.dupr_id
            p.rating.player_full_name = p.full_name
            return p
        except:
            logger.exception(d)
            raise


class Match(Base):
    __tablename__ = "match"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String(246))
    date: Mapped[str] = mapped_column(String(16))
    teams: Mapped[List["MatchTeam"]] = relationship(back_populates="match")
    match_type: Mapped[str] = mapped_column(default="")
    match_source: Mapped[str] = mapped_column(default="")
    match_score_added: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"Match {self.name} on {self.date}"

    @classmethod
    def get_by_id(cls, sess: Session, match_id: int) -> "Match":
        m = sess.execute(select(Match).where(
            Match.match_id == match_id)).scalar_one_or_none()
        return m

    @classmethod
    def from_json(cls, d: dict):

        try:
            m = Match()
            m.match_id = d.get("matchId")
            m.user_id = d.get("userId")
            m.display_identity = d.get("displayIdentity")
            m.confirmed = d.get("confirmed")
            m.date = date.fromisoformat(d.get("eventDate"))
            # need to try different fields...
            m.name = d.get("eventName")
            if not m.name:
                m.name = d.get("league")
            if not m.name:
                m.name = d.get("tournament", "")
            m.event_format = d.get("eventFormat")
            m.match_score_added = d.get("matchScoreAdded")
            m.match_source = d.get("matchSource")
            m.match_type = d.get("matchType")

            for jt in d.get("teams"):
                t = MatchTeam().from_json(jt)
                m.teams.append(t)
            return m

        except:
            logger.exception(d)
            raise


match_team_player = Table(
    "match_team_player",
    Base.metadata,
    Column("match_team_id", ForeignKey("match_team.id")),
    Column("player_id", ForeignKey("player.id"))
)


class MatchTeam(Base):
    __tablename__ = "match_team"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id = mapped_column(ForeignKey("match.id"))
    match: Mapped[Match] = relationship(back_populates="teams")
    score1: Mapped[int] = mapped_column()
    score2: Mapped[Optional[int]] = mapped_column()
    score3: Mapped[Optional[int]] = mapped_column()
    is_winner: Mapped[bool] = mapped_column()
    players: Mapped[List["Player"]] = relationship(
        secondary=match_team_player,
        back_populates="match_teams"
        )

    def __repr__(self) -> str:
        ps = ",".join([p.full_name for p in self.players])
        return f"Match Team {ps}"

    @classmethod
    def from_json(cls, d: dict):

        try:
            mt = MatchTeam()
            mt.score1 = d.get("game1")
            mt.score2 = d.get("game2")
            mt.score3 = d.get("game3")
            p = Player().from_json(d.get("player1"))
            mt.players.append(p)
            pdata = d.get("player2")
            if pdata:
                p2 = Player().from_json(pdata)
                mt.players.append(p2)
            mt.is_winner = d.get("winner")
            return mt

        except:
            logger.exception(d)
            raise


class MatchDetail(Base):
    """
    A denormalized table for match and players because this is the primary
    query that is useful.
    """

    __tablename__ = "match_detail"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("match.id"))
    match: Mapped["Match"] = relationship()
    # team 1 is the winning team
    team_1_score: Mapped[int] = mapped_column()
    team_2_score: Mapped[int] = mapped_column()

    team_1_player_1_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    team_1_player_2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player.id"))
    team_2_player_1_id: Mapped[int] = mapped_column(ForeignKey("player.id"))
    team_2_player_2_id: Mapped[Optional[int]] = mapped_column(ForeignKey("player.id"))

    def __repr__(self) -> str:
        return f"Match {self.name} on {self.date}"

    @classmethod
    def get_by_id(cls, sess: Session, match_id: int) -> "Match":
        m = sess.execute(select(Match).where(
            Match.match_id == match_id)).scalar_one_or_none()
        return m


class PlayerMetadataSnapshot(Base):
    __tablename__ = "player_metadata_snapshot"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_dupr_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    player_full_name: Mapped[Optional[str]] = mapped_column(String(128))
    player_metadata_json: Mapped[str] = mapped_column(Text, nullable=False)
    player_metadata_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    matches_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    matches_scope: Mapped[Optional[str]] = mapped_column(String(16))
    matches_start_date: Mapped[Optional[str]] = mapped_column(String(10))
    matches_end_date: Mapped[Optional[str]] = mapped_column(String(10))
    matches_count: Mapped[Optional[int]] = mapped_column(Integer)


class PlayerMatchRaw(Base):
    __tablename__ = "player_match_raw"
    __table_args__ = (
        UniqueConstraint("player_dupr_id", "match_id", name="uq_player_match_raw_player_match"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_dupr_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    match_id: Mapped[int] = mapped_column(Integer, nullable=False)
    match_json: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PlayerRatingHistory(Base):
    __tablename__ = "player_rating_history"
    __table_args__ = (
        UniqueConstraint(
            "player_dupr_id",
            "rating_type",
            "scope_start_date",
            "scope_end_date",
            "row_index",
            name="uq_player_rating_history_scope_row",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    player_dupr_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    rating_type: Mapped[str] = mapped_column(String(16), nullable=False)
    scope_start_date: Mapped[str] = mapped_column(String(10), nullable=False)
    scope_end_date: Mapped[str] = mapped_column(String(10), nullable=False)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    rating_date: Mapped[str] = mapped_column(String(10), nullable=False)
    match_date: Mapped[Optional[str]] = mapped_column(String(10))
    rating: Mapped[Optional[float]] = mapped_column(Float)
    changed_by_admin: Mapped[Optional[bool]] = mapped_column(Boolean)
    rating_history_json: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
