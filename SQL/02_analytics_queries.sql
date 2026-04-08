-- 1. Top Tracks
CREATE OR REPLACE VIEW v_top_played_track AS
(
SELECT track, COUNT(*) AS plays
FROM clean_listening_history
WHERE true_skip = 0
GROUP BY track
ORDER BY plays DESC
);

-- 2. Top Tracks by Playtime
CREATE OR REPLACE VIEW v_top_played_duration AS
(
SELECT track,
       artist,
       MAX(formatted_duration)           AS duration,
       CONCAT(
               FLOOR(SUM(plot_duration) / 60), ' hours & ',
               FLOOR(SUM(plot_duration) % 60), ' minutes'
       )                                 AS total_hours_listened,
       ROUND(SUM(plot_duration) / 60, 2) AS hours_for_plot,
       COUNT(*)                          AS total_plays
FROM clean_listening_history
GROUP BY track, artist
ORDER BY hours_for_plot DESC
);

-- 3. Most played Artists
CREATE OR REPLACE VIEW v_most_played_artist AS
(
SELECT artist, COUNT(*) AS plays
FROM clean_listening_history
WHERE true_skip = 0
GROUP BY artist
ORDER BY plays DESC
);

-- 4. Skip Ratio Track
CREATE OR REPLACE VIEW v_skip_ratio_track AS
(
SELECT track,
       artist,
       COUNT(*)                                    AS total_plays,
       SUM(true_skip)                              AS total_skips,
       ROUND((SUM(true_skip) / COUNT(*) * 100), 2) AS percentage
FROM clean_listening_history
GROUP BY track, artist
HAVING total_plays > 10
ORDER BY percentage DESC
);

-- 5. Skip Ratio Artist
CREATE OR REPLACE VIEW v_skip_ratio_artist AS
(
SELECT artist,
       COUNT(*) AS total_plays,
       SUM(true_skip) AS total_skips,
       ROUND((SUM(true_skip) / COUNT(*) * 100), 2) AS percentage
FROM clean_listening_history
GROUP BY artist
HAVING total_plays > 20
ORDER BY total_skips DESC
);
SELECT* FROM v_skip_ratio_artist;

-- 6. Total Plays per Hour
CREATE OR REPLACE VIEW v_hourly_plays AS
(
SELECT HOUR(timestamp) AS hour, COUNT(*) AS played_count
FROM clean_listening_history
WHERE true_skip = 0
GROUP BY HOUR(timestamp)
ORDER BY HOUR(timestamp)
);

-- 7. Top Track by Hour
CREATE OR REPLACE VIEW v_hourly_top_track AS
(
WITH HourlyCounts AS (SELECT HOUR(timestamp) as local_hour,
                             track,
                             COUNT(*)        AS total_plays
                      FROM clean_listening_history
                      WHERE true_skip = 0
                      GROUP BY HOUR(timestamp), track),
     RankedTracks AS (SELECT local_hour,
                             track,
                             total_plays,
                             ROW_NUMBER() OVER (PARTITION BY local_hour ORDER BY total_plays DESC) AS ranking
                      FROM HourlyCounts)
SELECT local_hour, track AS top_track, total_plays
FROM RankedTracks
WHERE ranking = 1
ORDER BY local_hour
);

-- 8. Days with Longest Music Sessions
CREATE OR REPLACE VIEW v_daily_session_duration AS
(
SELECT DATE(timestamp)                   as date,
       ROUND(SUM(plot_duration) / 60, 2) AS hours_for_plot,
       CONCAT(
               FLOOR(SUM(plot_duration) / 60), ' hours & ',
               FLOOR(SUM(plot_duration) % 60), ' minutes'
       )                                 AS duration_of_session
FROM clean_listening_history
GROUP BY date
ORDER BY date
);
