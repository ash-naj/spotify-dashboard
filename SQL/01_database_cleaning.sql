CREATE OR REPLACE VIEW clean_listening_history AS
SELECT
    id,

    -- Timezone changes
    CASE
        -- during Iran
        WHEN ts < '2025-09-17T11:28:00Z' THEN CONVERT_TZ(STR_TO_DATE(ts, '%Y-%m-%dT%H:%i:%sZ'), 'UTC', 'Asia/Tehran')
        -- during Turkey
        WHEN '2025-09-17T11:28:00Z' <= ts AND ts < '2025-10-01T10:00:00Z' THEN CONVERT_TZ(STR_TO_DATE(ts, '%Y-%m-%dT%H:%i:%sZ'), 'UTC', 'Europe/Istanbul')
        -- during Europe
        ELSE CONVERT_TZ(STR_TO_DATE(ts, '%Y-%m-%dT%H:%i:%sZ'), 'UTC', 'Europe/Vienna')
        END AS timestamp,

    ms_played AS ms_duration,

    -- creating 'plot_duration' that uses min:00 that the right part is a percentage.
    ROUND(ms_played / 60000, 2) AS plot_duration,

    -- creating 'formatted_duration' that uses min:sec.
    TIME_FORMAT(SEC_TO_TIME(ms_played / 1000), '%i:%s') AS formatted_duration,

    master_metadata_track_name AS track,
    master_metadata_album_artist_name AS artist,
    master_metadata_album_album_name AS album,
    spotify_track_uri as link,
    reason_start,
    reason_end,
    skipped,

    -- creating 'true_skip' that indicates if a song is skipped before 10 seconds of it being played
    IF (ms_played < 10000, 1, 0) AS true_skip
FROM listening_history;