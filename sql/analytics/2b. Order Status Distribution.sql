SELECT 
    st.order_status, 
    COUNT(*) AS order_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS status_percentage
FROM fact_orders fo
INNER JOIN status_table st ON fo.status_code = st.status_code
GROUP BY st.order_status
ORDER BY status_percentage DESC;