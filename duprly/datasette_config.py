from __future__ import annotations


def build_datasette_metadata(db_name: str) -> dict:
    """Build Datasette metadata with curated canned analytics queries."""
    queries = {
        "player_directory": {
            "title": "Player Directory",
            "description": (
                "Player name/ID lookup source for dashboard inputs with autocomplete and dropdowns."
            ),
            "hide_sql": True,
            "params": ["q", "limit"],
            "sql": """
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    player_label
                FROM v_player_directory
                WHERE (
                    NULLIF(:q, '') IS NULL
                    OR LOWER(player_full_name) LIKE '%' || LOWER(:q) || '%'
                    OR CAST(player_dupr_id AS TEXT) LIKE '%' || :q || '%'
                )
                ORDER BY player_full_name COLLATE NOCASE ASC, player_dupr_id ASC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 2000)
            """,
        },
        "club_directory": {
            "title": "Club Directory",
            "description": (
                "Club name/ID lookup source for dashboard inputs with autocomplete and dropdowns."
            ),
            "hide_sql": True,
            "params": ["q", "limit"],
            "sql": """
                SELECT
                    club_id,
                    club_name,
                    club_label
                FROM v_club_directory
                WHERE (
                    NULLIF(:q, '') IS NULL
                    OR LOWER(club_name) LIKE '%' || LOWER(:q) || '%'
                    OR CAST(club_id AS TEXT) LIKE '%' || :q || '%'
                )
                ORDER BY club_name COLLATE NOCASE ASC, club_id ASC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 1000)
            """,
        },
        "player_rating_over_time": {
            "title": "Player Rating Over Time",
            "description": (
                "Trend view for a player over time. Defaults to DOUBLES and full available date range."
            ),
            "hide_sql": True,
            "params": ["dupr_id", "rating_type", "start_date", "end_date", "limit"],
            "sql": """
                WITH base_scoped AS (
                    SELECT
                        vrp.*,
                        COALESCE(
                            CAST(json_extract(prh.rating_history_json, '$.matchId') AS INTEGER),
                            CAST(json_extract(prh.rating_history_json, '$.id') AS INTEGER)
                        ) AS context_match_id,
                        COALESCE(
                            CAST(json_extract(prh.rating_history_json, '$.reliabilityScore') AS REAL),
                            CAST(json_extract(prh.rating_history_json, '$.reliability') AS REAL),
                            CAST(json_extract(prh.rating_history_json, '$.reliabilityIndex') AS REAL)
                        ) AS reliability_score
                    FROM v_player_rating_points vrp
                    JOIN player_rating_history prh ON prh.id = vrp.rating_history_id
                    WHERE vrp.player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND vrp.rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                      AND vrp.rating_date BETWEEN COALESCE(NULLIF(:start_date, ''), '1970-01-01')
                                              AND COALESCE(NULLIF(:end_date, ''), date('now'))
                ),
                scoped AS (
                    SELECT *
                    FROM (
                        SELECT
                            b.*,
                            ROW_NUMBER() OVER (
                                PARTITION BY
                                    b.player_dupr_id,
                                    b.rating_type,
                                    b.rating_date,
                                    COALESCE(b.match_date, ''),
                                    COALESCE(CAST(b.rating AS TEXT), ''),
                                    COALESCE(CAST(b.changed_by_admin AS TEXT), ''),
                                    COALESCE(CAST(b.reliability_score AS TEXT), '')
                                ORDER BY b.fetched_at DESC, b.rating_history_id DESC
                            ) AS dedupe_rank
                        FROM base_scoped b
                    )
                    WHERE dedupe_rank = 1
                ),
                match_context AS (
                    SELECT
                        pmr.player_dupr_id,
                        pmr.match_id,
                        json_extract(pmr.match_json, '$.eventDate') AS event_date,
                        json_extract(pmr.match_json, '$.created') AS created_date,
                        json_extract(pmr.match_json, '$.modified') AS modified_date,
                        COALESCE(
                            NULLIF(json_extract(pmr.match_json, '$.eventName'), ''),
                            NULLIF(json_extract(pmr.match_json, '$.league'), ''),
                            NULLIF(json_extract(pmr.match_json, '$.tournament'), '')
                        ) AS event_title,
                        COALESCE(
                            NULLIF(json_extract(pmr.match_json, '$.location'), ''),
                            NULLIF(json_extract(pmr.match_json, '$.venue'), '')
                        ) AS location,
                        (
                            SELECT
                                CASE
                                    WHEN CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN json_extract(t.value, '$.player2.fullName')
                                    WHEN CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN json_extract(t.value, '$.player1.fullName')
                                    ELSE NULL
                                END
                            FROM json_each(pmr.match_json, '$.teams') t
                            WHERE CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                               OR CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                            LIMIT 1
                        ) AS partner_name,
                        (
                            SELECT group_concat(opponent_name, ' | ')
                            FROM (
                                SELECT
                                    TRIM(
                                        COALESCE(json_extract(o.value, '$.player1.fullName'), '')
                                        || CASE
                                            WHEN NULLIF(json_extract(o.value, '$.player2.fullName'), '') IS NOT NULL
                                            THEN ' & ' || json_extract(o.value, '$.player2.fullName')
                                            ELSE ''
                                        END
                                    ) AS opponent_name
                                FROM json_each(pmr.match_json, '$.teams') o
                                WHERE CAST(json_extract(o.value, '$.player1.id') AS INTEGER) != pmr.player_dupr_id
                                  AND CAST(json_extract(o.value, '$.player2.id') AS INTEGER) != pmr.player_dupr_id
                            )
                        ) AS opponents,
                        (
                            WITH player_team AS (
                                SELECT t.value AS team_value
                                FROM json_each(pmr.match_json, '$.teams') t
                                WHERE CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                                   OR CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                                LIMIT 1
                            ),
                            opponent_team AS (
                                SELECT t.value AS team_value
                                FROM json_each(pmr.match_json, '$.teams') t
                                WHERE CAST(json_extract(t.value, '$.player1.id') AS INTEGER) != pmr.player_dupr_id
                                  AND CAST(json_extract(t.value, '$.player2.id') AS INTEGER) != pmr.player_dupr_id
                                LIMIT 1
                            ),
                            scores AS (
                                SELECT
                                    COALESCE(
                                        NULLIF(CAST(json_extract((SELECT team_value FROM player_team), '$.game1') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM player_team), '$.game2') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM player_team), '$.game3') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM player_team), '$.game4') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM player_team), '$.game5') AS INTEGER), -1)
                                    ) AS player_score,
                                    COALESCE(
                                        NULLIF(CAST(json_extract((SELECT team_value FROM opponent_team), '$.game1') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM opponent_team), '$.game2') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM opponent_team), '$.game3') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM opponent_team), '$.game4') AS INTEGER), -1),
                                        NULLIF(CAST(json_extract((SELECT team_value FROM opponent_team), '$.game5') AS INTEGER), -1)
                                    ) AS opponent_score
                            )
                            SELECT
                                CASE
                                    WHEN player_score IS NULL OR opponent_score IS NULL THEN NULL
                                    ELSE printf('%d-%d', player_score, opponent_score)
                                END
                            FROM scores
                        ) AS score,
                        (
                            SELECT
                                CASE
                                    WHEN CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN CAST(json_extract(t.value, '$.player1.postMatchRating.singles') AS REAL)
                                    WHEN CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN CAST(json_extract(t.value, '$.player2.postMatchRating.singles') AS REAL)
                                    ELSE NULL
                                END
                            FROM json_each(pmr.match_json, '$.teams') t
                            WHERE CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                               OR CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                            LIMIT 1
                        ) AS post_singles,
                        (
                            SELECT
                                CASE
                                    WHEN CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN CAST(json_extract(t.value, '$.player1.postMatchRating.doubles') AS REAL)
                                    WHEN CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN CAST(json_extract(t.value, '$.player2.postMatchRating.doubles') AS REAL)
                                    ELSE NULL
                                END
                            FROM json_each(pmr.match_json, '$.teams') t
                            WHERE CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                               OR CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                            LIMIT 1
                        ) AS post_doubles,
                        (
                            WITH self_team AS (
                                SELECT t.value AS team_value
                                FROM json_each(pmr.match_json, '$.teams') t
                                WHERE CAST(json_extract(t.value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                                   OR CAST(json_extract(t.value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                                LIMIT 1
                            )
                            SELECT
                                CASE
                                    WHEN self_team.team_value IS NULL THEN NULL
                                    WHEN CAST(json_extract(self_team.team_value, '$.player1.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN json_object(
                                            'name', json_extract(self_team.team_value, '$.player2.fullName'),
                                            'dupr_id', CAST(json_extract(self_team.team_value, '$.player2.id') AS INTEGER),
                                            'dupr_code', json_extract(self_team.team_value, '$.player2.duprId'),
                                            'pre_singles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.preMatchSingleRatingPlayer2') AS REAL),
                                            'delta_singles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.matchSingleRatingImpactPlayer2') AS REAL),
                                            'post_singles', CAST(json_extract(self_team.team_value, '$.player2.postMatchRating.singles') AS REAL),
                                            'pre_doubles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.preMatchDoubleRatingPlayer2') AS REAL),
                                            'delta_doubles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.matchDoubleRatingImpactPlayer2') AS REAL),
                                            'post_doubles', CAST(json_extract(self_team.team_value, '$.player2.postMatchRating.doubles') AS REAL),
                                            'reliability_score', CAST(json_extract(self_team.team_value, '$.player2.reliabilityScore') AS REAL)
                                        )
                                    WHEN CAST(json_extract(self_team.team_value, '$.player2.id') AS INTEGER) = pmr.player_dupr_id
                                        THEN json_object(
                                            'name', json_extract(self_team.team_value, '$.player1.fullName'),
                                            'dupr_id', CAST(json_extract(self_team.team_value, '$.player1.id') AS INTEGER),
                                            'dupr_code', json_extract(self_team.team_value, '$.player1.duprId'),
                                            'pre_singles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.preMatchSingleRatingPlayer1') AS REAL),
                                            'delta_singles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.matchSingleRatingImpactPlayer1') AS REAL),
                                            'post_singles', CAST(json_extract(self_team.team_value, '$.player1.postMatchRating.singles') AS REAL),
                                            'pre_doubles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.preMatchDoubleRatingPlayer1') AS REAL),
                                            'delta_doubles', CAST(json_extract(self_team.team_value, '$.preMatchRatingAndImpact.matchDoubleRatingImpactPlayer1') AS REAL),
                                            'post_doubles', CAST(json_extract(self_team.team_value, '$.player1.postMatchRating.doubles') AS REAL),
                                            'reliability_score', CAST(json_extract(self_team.team_value, '$.player1.reliabilityScore') AS REAL)
                                        )
                                    ELSE NULL
                                END
                            FROM self_team
                        ) AS partner_tooltip_json,
                        (
                            SELECT json_group_array(
                                json_object(
                                    'name', x.name,
                                    'dupr_id', x.dupr_id,
                                    'dupr_code', x.dupr_code,
                                    'pre_singles', x.pre_singles,
                                    'delta_singles', x.delta_singles,
                                    'post_singles', x.post_singles,
                                    'pre_doubles', x.pre_doubles,
                                    'delta_doubles', x.delta_doubles,
                                    'post_doubles', x.post_doubles,
                                    'reliability_score', x.reliability_score
                                )
                            )
                            FROM (
                                SELECT
                                    json_extract(o.value, '$.player1.fullName') AS name,
                                    CAST(json_extract(o.value, '$.player1.id') AS INTEGER) AS dupr_id,
                                    json_extract(o.value, '$.player1.duprId') AS dupr_code,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.preMatchSingleRatingPlayer1') AS REAL) AS pre_singles,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.matchSingleRatingImpactPlayer1') AS REAL) AS delta_singles,
                                    CAST(json_extract(o.value, '$.player1.postMatchRating.singles') AS REAL) AS post_singles,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.preMatchDoubleRatingPlayer1') AS REAL) AS pre_doubles,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.matchDoubleRatingImpactPlayer1') AS REAL) AS delta_doubles,
                                    CAST(json_extract(o.value, '$.player1.postMatchRating.doubles') AS REAL) AS post_doubles,
                                    CAST(json_extract(o.value, '$.player1.reliabilityScore') AS REAL) AS reliability_score
                                FROM json_each(pmr.match_json, '$.teams') o
                                WHERE CAST(json_extract(o.value, '$.player1.id') AS INTEGER) != pmr.player_dupr_id
                                  AND CAST(json_extract(o.value, '$.player2.id') AS INTEGER) != pmr.player_dupr_id
                                UNION ALL
                                SELECT
                                    json_extract(o.value, '$.player2.fullName') AS name,
                                    CAST(json_extract(o.value, '$.player2.id') AS INTEGER) AS dupr_id,
                                    json_extract(o.value, '$.player2.duprId') AS dupr_code,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.preMatchSingleRatingPlayer2') AS REAL) AS pre_singles,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.matchSingleRatingImpactPlayer2') AS REAL) AS delta_singles,
                                    CAST(json_extract(o.value, '$.player2.postMatchRating.singles') AS REAL) AS post_singles,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.preMatchDoubleRatingPlayer2') AS REAL) AS pre_doubles,
                                    CAST(json_extract(o.value, '$.preMatchRatingAndImpact.matchDoubleRatingImpactPlayer2') AS REAL) AS delta_doubles,
                                    CAST(json_extract(o.value, '$.player2.postMatchRating.doubles') AS REAL) AS post_doubles,
                                    CAST(json_extract(o.value, '$.player2.reliabilityScore') AS REAL) AS reliability_score
                                FROM json_each(pmr.match_json, '$.teams') o
                                WHERE CAST(json_extract(o.value, '$.player1.id') AS INTEGER) != pmr.player_dupr_id
                                  AND CAST(json_extract(o.value, '$.player2.id') AS INTEGER) != pmr.player_dupr_id
                                  AND NULLIF(json_extract(o.value, '$.player2.fullName'), '') IS NOT NULL
                            ) x
                        ) AS opponents_tooltip_json
                    FROM player_match_raw pmr
                ),
                normalized_context AS (
                    SELECT
                        self_player.dupr_id AS player_dupr_id,
                        m.match_id,
                        m.date AS event_date,
                        NULL AS created_date,
                        NULL AS modified_date,
                        m.name AS event_title,
                        NULL AS location,
                        (
                            SELECT partner.full_name
                            FROM match_team_player mtp_partner
                            JOIN player partner ON partner.id = mtp_partner.player_id
                            WHERE mtp_partner.match_team_id = self_team.id
                              AND mtp_partner.player_id != self_player.id
                            LIMIT 1
                        ) AS partner_name,
                        (
                            SELECT group_concat(opp.full_name, ' & ')
                            FROM match_team_player mtp_opp
                            JOIN player opp ON opp.id = mtp_opp.player_id
                            WHERE mtp_opp.match_team_id = opp_team.id
                        ) AS opponents,
                        CASE
                            WHEN self_team.score1 IS NULL OR opp_team.score1 IS NULL THEN NULL
                            ELSE printf('%d-%d', self_team.score1, opp_team.score1)
                        END AS score,
                        NULL AS post_singles,
                        NULL AS post_doubles,
                        (
                            SELECT json_object(
                                'name', partner.full_name,
                                'dupr_id', partner.dupr_id,
                                'dupr_code', NULL,
                                'pre_singles', NULL,
                                'delta_singles', NULL,
                                'post_singles', NULL,
                                'pre_doubles', NULL,
                                'delta_doubles', NULL,
                                'post_doubles', NULL,
                                'reliability_score', NULL
                            )
                            FROM match_team_player mtp_partner
                            JOIN player partner ON partner.id = mtp_partner.player_id
                            WHERE mtp_partner.match_team_id = self_team.id
                              AND mtp_partner.player_id != self_player.id
                            LIMIT 1
                        ) AS partner_tooltip_json,
                        (
                            SELECT json_group_array(
                                json_object(
                                    'name', opp.full_name,
                                    'dupr_id', opp.dupr_id,
                                    'dupr_code', NULL,
                                    'pre_singles', NULL,
                                    'delta_singles', NULL,
                                    'post_singles', NULL,
                                    'pre_doubles', NULL,
                                    'delta_doubles', NULL,
                                    'post_doubles', NULL,
                                    'reliability_score', NULL
                                )
                            )
                            FROM match_team_player mtp_opp
                            JOIN player opp ON opp.id = mtp_opp.player_id
                            WHERE mtp_opp.match_team_id = opp_team.id
                        ) AS opponents_tooltip_json
                    FROM match_team_player mtp_self
                    JOIN player self_player ON self_player.id = mtp_self.player_id
                    JOIN match_team self_team ON self_team.id = mtp_self.match_team_id
                    JOIN "match" m ON m.id = self_team.match_id
                    LEFT JOIN match_team opp_team
                      ON opp_team.match_id = self_team.match_id
                     AND opp_team.id != self_team.id
                ),
                all_context AS (
                    SELECT * FROM match_context
                    UNION ALL
                    SELECT * FROM normalized_context
                ),
                context_dedup AS (
                    SELECT *
                    FROM (
                        SELECT
                            ac.*,
                            ROW_NUMBER() OVER (
                                PARTITION BY ac.player_dupr_id, ac.match_id
                                ORDER BY
                                    CASE WHEN ac.modified_date IS NULL THEN 1 ELSE 0 END ASC,
                                    ac.modified_date DESC
                            ) AS context_rank
                        FROM all_context ac
                    )
                    WHERE context_rank = 1
                ),
                rating_candidates AS (
                    SELECT
                        s.rating_history_id,
                        c.match_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY s.rating_history_id
                            ORDER BY
                                ABS(julianday(c.event_date) - julianday(COALESCE(s.match_date, s.rating_date))) ASC,
                                CASE
                                    WHEN s.rating_type = 'DOUBLES' THEN ABS(c.post_doubles - s.rating)
                                    ELSE ABS(c.post_singles - s.rating)
                                END ASC,
                                CASE WHEN c.modified_date IS NULL THEN 1 ELSE 0 END ASC,
                                c.modified_date DESC,
                                c.match_id DESC
                        ) AS candidate_rank
                    FROM scoped s
                    JOIN context_dedup c
                      ON c.player_dupr_id = s.player_dupr_id
                     AND c.event_date BETWEEN date(COALESCE(s.match_date, s.rating_date), '-7 day')
                                         AND date(COALESCE(s.match_date, s.rating_date), '+7 day')
                     AND s.rating IS NOT NULL
                     AND (
                        (s.rating_type = 'DOUBLES' AND c.post_doubles IS NOT NULL AND ABS(c.post_doubles - s.rating) <= 0.08)
                        OR
                        (s.rating_type = 'SINGLES' AND c.post_singles IS NOT NULL AND ABS(c.post_singles - s.rating) <= 0.08)
                     )
                ),
                date_candidates AS (
                    SELECT
                        s.rating_history_id,
                        c.match_id,
                        ROW_NUMBER() OVER (
                            PARTITION BY s.rating_history_id
                            ORDER BY
                                ABS(julianday(c.event_date) - julianday(COALESCE(s.match_date, s.rating_date))) ASC,
                                CASE WHEN c.modified_date IS NULL THEN 1 ELSE 0 END ASC,
                                c.modified_date DESC,
                                c.match_id DESC
                        ) AS candidate_rank
                    FROM scoped s
                    JOIN context_dedup c
                      ON c.player_dupr_id = s.player_dupr_id
                     AND c.event_date BETWEEN date(COALESCE(s.match_date, s.rating_date), '-3 day')
                                         AND date(COALESCE(s.match_date, s.rating_date), '+3 day')
                ),
                resolved AS (
                    SELECT
                        s.*,
                        CASE
                            WHEN s.context_match_id IS NOT NULL THEN s.context_match_id
                            WHEN rc.match_id IS NOT NULL THEN rc.match_id
                            WHEN dc.match_id IS NOT NULL THEN dc.match_id
                            ELSE NULL
                        END AS resolved_match_id,
                        CASE
                            WHEN s.context_match_id IS NOT NULL THEN 'direct'
                            WHEN rc.match_id IS NOT NULL THEN 'rating+date'
                            WHEN dc.match_id IS NOT NULL THEN 'date-only'
                            ELSE 'no-match'
                        END AS resolution_method
                    FROM scoped s
                    LEFT JOIN rating_candidates rc
                      ON rc.rating_history_id = s.rating_history_id
                     AND rc.candidate_rank = 1
                    LEFT JOIN date_candidates dc
                      ON dc.rating_history_id = s.rating_history_id
                     AND dc.candidate_rank = 1
                ),
                enriched AS (
                    SELECT
                        r.rating_history_id,
                        r.player_dupr_id,
                        r.player_full_name,
                        r.club_id,
                        r.rating_type,
                        r.rating_date,
                        r.match_date,
                        r.rating,
                        r.reliability_score,
                        r.changed_by_admin,
                        r.row_index,
                        r.resolved_match_id AS match_id,
                        COALESCE(
                            (
                                SELECT mc.event_date
                                FROM context_dedup mc
                                WHERE mc.player_dupr_id = r.player_dupr_id
                                  AND mc.match_id = r.resolved_match_id
                                LIMIT 1
                            ),
                            r.match_date
                        ) AS resolved_match_date,
                        (
                            SELECT mc.created_date
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS created_date,
                        (
                            SELECT mc.modified_date
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS modified_date,
                        (
                            SELECT mc.event_title
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS event_title,
                        (
                            SELECT mc.location
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS location,
                        (
                            SELECT mc.partner_name
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS partner_name,
                        (
                            SELECT mc.opponents
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS opponents,
                        (
                            SELECT mc.score
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS score,
                        (
                            SELECT mc.partner_tooltip_json
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS partner_tooltip_json,
                        (
                            SELECT mc.opponents_tooltip_json
                            FROM context_dedup mc
                            WHERE mc.player_dupr_id = r.player_dupr_id
                              AND mc.match_id = r.resolved_match_id
                            LIMIT 1
                        ) AS opponents_tooltip_json,
                        r.resolution_method
                    FROM resolved r
                ),
                final_rows AS (
                    SELECT *
                    FROM (
                        SELECT
                            e.*,
                            ROW_NUMBER() OVER (
                                PARTITION BY COALESCE(CAST(e.match_id AS TEXT), 'rh:' || CAST(e.rating_history_id AS TEXT))
                                ORDER BY e.rating_date DESC, e.row_index DESC, e.rating_history_id DESC
                            ) AS match_dedupe_rank
                        FROM enriched e
                    )
                    WHERE match_dedupe_rank = 1
                ),
                final_metrics AS (
                    SELECT
                        f.*,
                        CASE
                            WHEN f.rating IS NULL THEN NULL
                            ELSE f.rating - LAG(f.rating) OVER (
                                ORDER BY f.rating_date ASC, f.row_index ASC, f.rating_history_id ASC
                            )
                        END AS rating_change
                    FROM final_rows f
                )
                SELECT
                    e.player_dupr_id,
                    e.player_full_name,
                    e.club_id,
                    e.rating_type,
                    e.rating_date,
                    e.resolved_match_date AS match_date,
                    e.created_date,
                    e.modified_date,
                    COALESCE(e.event_title, '[missing]') AS event_title,
                    COALESCE(e.location, '[missing]') AS location,
                    (
                        SELECT vrp_latest.rating
                        FROM v_player_rating_points vrp_latest
                        WHERE vrp_latest.player_dupr_id = e.player_dupr_id
                          AND vrp_latest.rating_type = e.rating_type
                        ORDER BY
                            vrp_latest.rating_date DESC,
                            vrp_latest.row_index DESC,
                            vrp_latest.rating_history_id DESC
                        LIMIT 1
                    ) AS player_latest_rating,
                    (
                        SELECT vrp_latest.rating_date
                        FROM v_player_rating_points vrp_latest
                        WHERE vrp_latest.player_dupr_id = e.player_dupr_id
                          AND vrp_latest.rating_type = e.rating_type
                        ORDER BY
                            vrp_latest.rating_date DESC,
                            vrp_latest.row_index DESC,
                            vrp_latest.rating_history_id DESC
                        LIMIT 1
                    ) AS player_latest_rating_date,
                    e.rating,
                    ROUND(e.rating_change, 6) AS rating_change,
                    e.reliability_score,
                    e.changed_by_admin,
                    e.row_index,
                    e.match_id,
                    CASE
                        WHEN e.changed_by_admin IS 1 THEN 'yes'
                        WHEN e.changed_by_admin IS 0 THEN 'no'
                        ELSE 'unknown'
                    END AS score_admin_changed,
                    COALESCE(e.partner_name, '[missing]') AS partner_name,
                    COALESCE(e.opponents, '[missing]') AS opponents,
                    COALESCE(e.score, '[missing]') AS score,
                    CASE
                        WHEN e.match_id IS NULL
                          OR NULLIF(e.partner_name, '') IS NULL
                          OR NULLIF(e.opponents, '') IS NULL
                          OR NULLIF(e.score, '') IS NULL
                        THEN 'missing'
                        ELSE 'ok'
                    END AS context_status,
                    e.resolution_method,
                    e.partner_tooltip_json,
                    e.opponents_tooltip_json
                FROM final_metrics e
                ORDER BY e.rating_date ASC, e.row_index ASC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 1000)
            """,
        },
        "player_rating_summary": {
            "title": "Player Rating Summary",
            "description": "First/latest/delta/count summary for a player in the selected scope.",
            "hide_sql": True,
            "params": ["dupr_id", "rating_type", "start_date", "end_date"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_rating_points
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                      AND rating_date BETWEEN COALESCE(NULLIF(:start_date, ''), '1970-01-01')
                                          AND COALESCE(NULLIF(:end_date, ''), date('now'))
                ),
                ranked AS (
                    SELECT
                        scoped.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date ASC, row_index ASC, rating_history_id ASC
                        ) AS rn_first,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date DESC, row_index DESC, rating_history_id DESC
                        ) AS rn_last
                    FROM scoped
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    rating_type,
                    COUNT(*) AS points,
                    MAX(CASE WHEN rn_first = 1 THEN rating END) AS first_rating,
                    MAX(CASE WHEN rn_last = 1 THEN rating END) AS latest_rating,
                    (
                        MAX(CASE WHEN rn_last = 1 THEN rating END) -
                        MAX(CASE WHEN rn_first = 1 THEN rating END)
                    ) AS delta_rating,
                    MIN(rating_date) AS first_rating_date,
                    MAX(rating_date) AS latest_rating_date
                FROM ranked
                GROUP BY player_dupr_id, player_full_name, club_id, rating_type
            """,
        },
        "player_recent_form": {
            "title": "Player Recent Form",
            "description": "Recent match outcomes and win rate for a player (default last 90 days).",
            "hide_sql": True,
            "params": ["dupr_id", "days"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_match_results
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND match_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    COUNT(DISTINCT match_id) AS matches,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
                    ROUND(
                        1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                        NULLIF(COUNT(DISTINCT match_id), 0),
                        4
                    ) AS win_rate,
                    MAX(match_date) AS last_match_date
                FROM scoped
                GROUP BY player_dupr_id, player_full_name, club_id
            """,
        },
        "player_partner_breakdown": {
            "title": "Player Partner Breakdown",
            "description": "How a player performs with each partner over a recent time window.",
            "hide_sql": True,
            "params": ["dupr_id", "days", "min_matches", "limit"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_match_results
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND match_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                ),
                pairs AS (
                    SELECT
                        s.player_dupr_id,
                        s.player_full_name,
                        s.club_id,
                        partner.dupr_id AS partner_dupr_id,
                        partner.full_name AS partner_full_name,
                        s.match_id,
                        s.match_date,
                        s.is_winner
                    FROM scoped s
                    JOIN match_team_player mtp_partner
                      ON mtp_partner.match_team_id = s.team_id
                     AND mtp_partner.player_id != s.player_id
                    JOIN player partner ON partner.id = mtp_partner.player_id
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    partner_dupr_id,
                    partner_full_name,
                    COUNT(DISTINCT match_id) AS matches,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
                    ROUND(
                        1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                        NULLIF(COUNT(DISTINCT match_id), 0),
                        4
                    ) AS win_rate,
                    MAX(match_date) AS last_match_date
                FROM pairs
                GROUP BY
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    partner_dupr_id,
                    partner_full_name
                HAVING COUNT(DISTINCT match_id) >= COALESCE(CAST(NULLIF(:min_matches, '') AS INTEGER), 1)
                ORDER BY matches DESC, win_rate DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "player_opponent_breakdown": {
            "title": "Player Opponent Breakdown",
            "description": "How a player performs against specific opponents over a recent time window.",
            "hide_sql": True,
            "params": ["dupr_id", "days", "min_matches", "limit"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_match_results
                    WHERE player_dupr_id = CAST(:dupr_id AS INTEGER)
                      AND match_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                ),
                opponents AS (
                    SELECT
                        s.player_dupr_id,
                        s.player_full_name,
                        s.club_id,
                        opp.player_dupr_id AS opponent_dupr_id,
                        opp.player_full_name AS opponent_full_name,
                        s.match_id,
                        s.match_date,
                        s.is_winner
                    FROM scoped s
                    JOIN v_player_match_results opp
                      ON opp.match_db_id = s.match_db_id
                     AND opp.team_id != s.team_id
                )
                SELECT
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    opponent_dupr_id,
                    opponent_full_name,
                    COUNT(DISTINCT match_id) AS matches,
                    SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) AS wins,
                    SUM(CASE WHEN is_winner THEN 0 ELSE 1 END) AS losses,
                    ROUND(
                        1.0 * SUM(CASE WHEN is_winner THEN 1 ELSE 0 END) /
                        NULLIF(COUNT(DISTINCT match_id), 0),
                        4
                    ) AS win_rate,
                    MAX(match_date) AS last_match_date
                FROM opponents
                GROUP BY
                    player_dupr_id,
                    player_full_name,
                    club_id,
                    opponent_dupr_id,
                    opponent_full_name
                HAVING COUNT(DISTINCT match_id) >= COALESCE(CAST(NULLIF(:min_matches, '') AS INTEGER), 1)
                ORDER BY matches DESC, win_rate DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "club_top_risers": {
            "title": "Club Top Risers",
            "description": "Players with the biggest rating increase over a recent window (default doubles, 90 days).",
            "hide_sql": True,
            "params": ["club_id", "days", "rating_type", "limit"],
            "sql": """
                WITH scoped AS (
                    SELECT *
                    FROM v_player_rating_points
                    WHERE rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                      AND rating_date >= date(
                          'now',
                          printf('-%d day', COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90))
                      )
                      AND (
                          NULLIF(:club_id, '') IS NULL OR
                          club_id = CAST(:club_id AS INTEGER)
                      )
                ),
                ranked AS (
                    SELECT
                        scoped.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date ASC, row_index ASC, rating_history_id ASC
                        ) AS rn_first,
                        ROW_NUMBER() OVER (
                            PARTITION BY player_dupr_id, rating_type
                            ORDER BY rating_date DESC, row_index DESC, rating_history_id DESC
                        ) AS rn_last
                    FROM scoped
                ),
                summarized AS (
                    SELECT
                        player_dupr_id,
                        player_full_name,
                        club_id,
                        rating_type,
                        COUNT(*) AS points,
                        MAX(CASE WHEN rn_first = 1 THEN rating END) AS first_rating,
                        MAX(CASE WHEN rn_last = 1 THEN rating END) AS latest_rating,
                        (
                            MAX(CASE WHEN rn_last = 1 THEN rating END) -
                            MAX(CASE WHEN rn_first = 1 THEN rating END)
                        ) AS delta_rating,
                        MIN(rating_date) AS first_rating_date,
                        MAX(rating_date) AS latest_rating_date
                    FROM ranked
                    GROUP BY player_dupr_id, player_full_name, club_id, rating_type
                )
                SELECT *
                FROM summarized
                WHERE points >= 2
                ORDER BY delta_rating DESC, points DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "club_rating_snapshot": {
            "title": "Club Rating Snapshot",
            "description": "Club-level player counts and average singles/doubles ratings.",
            "hide_sql": True,
            "params": ["club_id", "limit"],
            "sql": """
                SELECT *
                FROM v_club_rating_snapshot
                WHERE (NULLIF(:club_id, '') IS NULL OR club_id = CAST(:club_id AS INTEGER))
                ORDER BY avg_doubles_rating DESC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
        "players_needing_more_data": {
            "title": "Players Needing More Data",
            "description": "Find players with sparse recent matches/rating points to target more activity.",
            "hide_sql": True,
            "params": ["days", "min_matches", "min_rating_points", "rating_type", "limit"],
            "sql": """
                WITH window AS (
                    SELECT COALESCE(CAST(NULLIF(:days, '') AS INTEGER), 90) AS days
                ),
                match_counts AS (
                    SELECT
                        pmr.player_dupr_id,
                        COUNT(DISTINCT pmr.match_id) AS matches_recent
                    FROM v_player_match_results pmr, window w
                    WHERE pmr.match_date >= date('now', printf('-%d day', w.days))
                    GROUP BY pmr.player_dupr_id
                ),
                rating_counts AS (
                    SELECT
                        vrp.player_dupr_id,
                        COUNT(*) AS rating_points_recent,
                        MAX(vrp.rating_date) AS last_rating_date
                    FROM v_player_rating_points vrp, window w
                    WHERE vrp.rating_type = UPPER(COALESCE(NULLIF(:rating_type, ''), 'DOUBLES'))
                      AND vrp.rating_date >= date('now', printf('-%d day', w.days))
                    GROUP BY vrp.player_dupr_id
                )
                SELECT
                    p.dupr_id AS player_dupr_id,
                    p.full_name AS player_full_name,
                    p.club_id,
                    COALESCE(mc.matches_recent, 0) AS matches_recent,
                    COALESCE(rc.rating_points_recent, 0) AS rating_points_recent,
                    rc.last_rating_date
                FROM player p
                LEFT JOIN match_counts mc ON mc.player_dupr_id = p.dupr_id
                LEFT JOIN rating_counts rc ON rc.player_dupr_id = p.dupr_id
                WHERE COALESCE(mc.matches_recent, 0) < COALESCE(CAST(NULLIF(:min_matches, '') AS INTEGER), 5)
                   OR COALESCE(rc.rating_points_recent, 0) < COALESCE(CAST(NULLIF(:min_rating_points, '') AS INTEGER), 5)
                ORDER BY matches_recent ASC, rating_points_recent ASC, p.full_name ASC
                LIMIT COALESCE(CAST(NULLIF(:limit, '') AS INTEGER), 200)
            """,
        },
    }

    return {
        "title": "DUPR Pickleball Analytics",
        "description": (
            "Question-driven local analytics for player trends, recent form, partner/opponent impact, and club movement."
        ),
        "plugins": {
            "datasette-vega": {
                "note": "Trend queries emit chart-friendly columns (rating_date, rating, rating_type)."
            }
        },
        "databases": {
            db_name: {
                "tables": {
                    "rating": {
                        "description": (
                            "Current player ratings with cached player identity columns for easier browsing."
                        )
                    },
                    "v_player_directory": {
                        "description": "Player name/ID labels for fast local lookup controls."
                    },
                    "v_club_directory": {
                        "description": "Club name/ID labels resolved from saved local metadata."
                    },
                    "v_player_rating_points": {
                        "description": "Row-level rating history points joined to player identity."
                    },
                    "v_player_match_results": {
                        "description": "Row-level player match results for outcome and trend analysis."
                    },
                },
                "queries": queries,
            }
        },
    }
