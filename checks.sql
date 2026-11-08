-- 1. Row counts per council, compared with the counts recorded at the pull: Bristol 4,472, Cardiff 3,526, Newport 1,386, Bridgend 1,363 and Vale of Glamorgan 1,347 (12,094 in all).
-- Found (8 November 2026): all five councils match the API's counts, 12,094 in total.
SELECT e.authority_id_code, COUNT(*) AS n, a.establishment_count, a.authority_name,
    CASE
        WHEN COUNT(*) = a.establishment_count THEN 'Count Correct'
        ELSE 'Count Incorrect'
    END AS count_check
FROM establishments as e
INNER JOIN authorities as a ON e.authority_id_code=a.authority_id_code
GROUP BY a.authority_name;

-- 2. Rating values: every distinct value and how many of each.
-- Found (8 November 2026): 10,299 ratings from 0 to 5, plus AwaitingInspection 1,390, Exempt 400 and AwaitingPublication 5 (12,094 in total).
SELECT rating_value, COUNT(*) AS n
FROM establishments
GROUP BY rating_value;

-- 3. Missing data: establishments with no postcode or no rating date.
-- Found (8 November 2026): 256 missing postcodes, 1,705 partial postcodes and 1,795 placeholder rating dates.
SELECT COUNT(*) AS n,
    CASE
        WHEN post_code IS NULL THEN 'Post Code Null'
        WHEN post_code = '' THEN 'Post Code Null'
        WHEN length(trim(post_code)) < 7 THEN 'Post Code Incomplete'
        ELSE 'Post Code Correct'
    END AS post_code_check,
    CASE
        WHEN date(rating_date) <= '1901-01-01' THEN 'Rating Date Placeholder'
        WHEN rating_date IS NULL THEN 'Rating Date Null'
        WHEN rating_date = '' THEN 'Rating Date Null'
        ELSE 'Rating Date Correct'
    END AS rating_date_check
FROM establishments
GROUP BY post_code_check, rating_date_check;

-- 4. Duplicates: the same business name and postcode appearing more than once.
-- Found (8 November 2026): 29 pairs. In 12, one record is rated and the other is awaiting inspection or exempt, 2 pairs are both awaiting inspection, and 15 are both rated.
SELECT COUNT(*) AS n, establishment_name, post_code,
    GROUP_CONCAT(date(rating_date), ' | ') AS rating_dates,
    GROUP_CONCAT(rating_value, ' | ') AS rating_values
FROM establishments
GROUP BY establishment_name, post_code
HAVING COUNT(*) > 1;

-- 4b. Stricter duplicates: the same business name, postcode and rating date appearing more than once.
-- Found (8 November 2026): 5 pairs.
SELECT COUNT(*) AS n, establishment_name, post_code, rating_date,
    GROUP_CONCAT(rating_value, ' | ') AS rating_values
FROM establishments
GROUP BY establishment_name, post_code, rating_date
HAVING COUNT(*) > 1;

-- 5. Dates: rating dates in the future, or more than five years old (placeholder dates left out).
-- Found (8 November 2026): none in the future and 636 more than five years old, out of 12,094.
SELECT 
    SUM(CASE WHEN date(rating_date) > date('now') THEN 1 ELSE 0 END) AS in_future,
    SUM(CASE WHEN date(rating_date) < date('now', '-5 years') AND date(rating_date) > '1901-01-01' THEN 1 ELSE 0 END) AS five_years_old,
    COUNT(*) AS total
FROM establishments;

-- 6. Establishments whose authority code has no matching council (LEFT JOIN).
-- Found (8 November 2026): none.
SELECT COUNT(*) AS n
FROM establishments as e
LEFT JOIN authorities as a ON a.authority_id_code=e.authority_id_code
WHERE a.authority_id_code IS NULL;