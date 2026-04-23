USE defaultdb;
-- 1. Top Tracks | Done
CREATE OR REPLACE VIEW v_top_tracks AS
(
SELECT track,
       SUM(ms_duration) / (1000 * 60 * 60) AS total_hours,
       artist
FROM clean_listening_history
WHERE true_skip = 0
GROUP BY track, artist
ORDER BY total_hours DESC
);

-- 2. Top Tracks by Playtime - only for CSV outputs
CREATE OR REPLACE VIEW v_top_track_duration AS
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
WHERE true_skip = 0
GROUP BY track, artist
ORDER BY hours_for_plot DESC
);

-- 3. Most played Artists | Done
CREATE OR REPLACE VIEW v_top_artists AS
(
SELECT artist,
       SUM(ms_duration) / (1000 * 60 * 60) AS total_hours
FROM clean_listening_history
WHERE true_skip = 0
GROUP BY artist
ORDER BY total_hours DESC
);
SELECT* FROM v_top_artists;

-- 4. Skip Ratio Track - shadowed by weighted version
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

-- 5. Skip Ratio Artist - shadowed by weighted version
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

-- 6. Weighted Artist Skip percentage | Done
CREATE OR REPLACE VIEW v_weighted_artist_skip_percentage AS
(
SELECT artist,
       COUNT(*) AS total_plays,
       SUM(true_skip) AS total_skips,
       -- I'm using LOG to normalize the play count, to avoid having artists with high play counts at the top of the list.
       -- Albeit, LOG has no natural ceiling, so to get a clean percentage we use the (Max total play(most played artist)) in the dataset as the divisor.
       -- +1 guards against LOG(0). OVER() applies MAX across all artists globally
       -- result is a 0–100 score: higher = listened to often AND rarely skipped
       ROUND(
               (1 - SUM(true_skip) / COUNT(*)) * LOG(COUNT(*) + 1) / LOG(MAX(COUNT(*)) OVER () + 1) *100 , 2
       ) AS weighted_skip_percentage
FROM clean_listening_history
GROUP BY artist
HAVING total_plays > 20
ORDER BY weighted_skip_percentage DESC
    );


-- 7. Weighted Track Skip percentage | Done
CREATE OR REPLACE VIEW v_weighted_track_skip_percentage AS
(
SELECT track,
       artist,
       COUNT(*) AS total_plays,
       SUM(true_skip) AS total_skips,
       ROUND(
               (1 - SUM(true_skip) / COUNT(*)) * LOG(COUNT(*) + 1) / LOG(MAX(COUNT(*)) OVER () + 1) *100 , 2
       ) AS weighted_skip_percentage
FROM clean_listening_history
GROUP BY track, artist
HAVING COUNT(*) > 20
ORDER BY weighted_skip_percentage DESC
    );

-- 8. Total Plays per Hour
CREATE OR REPLACE VIEW v_hourly_plays AS
SELECT
    HOUR(timestamp) AS hour,
    COUNT(*) AS all_time_plays,
    SUM(IF(timestamp >= (SELECT MAX(timestamp) FROM clean_listening_history) - INTERVAL 30 DAY, 1, 0)) AS last_30_days_plays,
    SUM(IF(timestamp >= (SELECT MAX(timestamp) FROM clean_listening_history) - INTERVAL 2 MONTH, 1, 0)) AS last_60_days_plays
FROM clean_listening_history
WHERE true_skip = 0
GROUP BY HOUR(timestamp)
ORDER BY hour;

-- 9. Top Track by Hour
CREATE OR REPLACE VIEW v_hourly_top_track AS
(
WITH HourlyCounts AS (SELECT HOUR(timestamp) as local_hour,
                             track,
                             artist,
                             COUNT(*)        AS total_plays
                      FROM clean_listening_history
                      WHERE true_skip = 0
                      GROUP BY HOUR(timestamp), track, artist),
     RankedTracks AS (SELECT local_hour,
                             track,
                             artist,
                             total_plays,
                             ROW_NUMBER() OVER (PARTITION BY local_hour ORDER BY total_plays DESC) AS ranking
                      FROM HourlyCounts)
SELECT local_hour, track AS top_track, artist, total_plays
FROM RankedTracks
WHERE ranking = 1
ORDER BY local_hour
);

-- 11. Most played artist each month
CREATE OR REPLACE VIEW v_monthly_top_artist AS
(
WITH monthlycount AS (SELECT YEAR(timestamp) AS year,
                            MONTH(timestamp) as month,
                             artist,
                             COUNT(*)        AS total_plays
                      FROM clean_listening_history
                      WHERE true_skip = 0
                      GROUP BY year, month, artist),
     RankedArtists AS (SELECT year,
                           month,
                             artist,
                             total_plays,
                             ROW_NUMBER() OVER (PARTITION BY year, month ORDER BY total_plays DESC) AS ranking
                      FROM monthlycount)
SELECT year, month, artist AS top_artist
FROM RankedArtists
WHERE ranking = 1
ORDER BY year, month
);

-- 12. Most played track each month
CREATE OR REPLACE VIEW v_monthly_top_track AS
(
WITH monthlycount AS (SELECT YEAR(timestamp) AS year,
                             MONTH(timestamp) as month,
                             track,
                             artist,
                             COUNT(*)        AS total_plays
                      FROM clean_listening_history
                      WHERE true_skip = 0
                      GROUP BY year, month, track, artist),
     rankedtrack AS (SELECT year,
                              month,
                              track,
                              artist,
                              total_plays,
                              ROW_NUMBER() OVER (PARTITION BY year, month ORDER BY total_plays DESC) AS ranking
                       FROM monthlycount)
SELECT year, month, track AS top_track, artist
FROM rankedtrack
WHERE ranking = 1
ORDER BY year, month
);
SELECT* FROM v_monthly_top_track;

-- 13. Data for Listening timeline Graph
CREATE OR REPLACE VIEW v_daily_listening_summary AS
    SELECT
        DATE(timestamp) AS date,
        SUM(ms_duration) / (1000 * 60 * 60) AS hours_for_plot,
        CONCAT(
                   FLOOR(SUM(plot_duration) / 60), ' hours & ',
                   FLOOR(SUM(plot_duration) % 60), ' minutes'
           )                                 AS duration_of_session
    FROM clean_listening_history
    GROUP BY
        DATE(timestamp)
    ORDER BY
        date;