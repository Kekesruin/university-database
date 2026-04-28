WITH RECURSIVE depth AS (
    SELECT 
        table_name,
        0 AS depth
    FROM information_schema.tables
    WHERE table_schema = 'public' 
      AND table_type = 'BASE TABLE'
      AND table_name NOT IN (
          SELECT tc.table_name 
          FROM information_schema.table_constraints tc
          WHERE tc.constraint_type = 'FOREIGN KEY'
      )
    
    UNION
    
    SELECT 
        tc.table_name,
        d.depth + 1
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu 
        ON ccu.constraint_name = tc.constraint_name
    JOIN depth d ON ccu.table_name = d.table_name
    WHERE tc.constraint_type = 'FOREIGN KEY' 
      AND tc.table_name != ccu.table_name
),
min_depth AS (
    SELECT 
        table_name, 
        MIN(depth) AS depth
    FROM depth
    GROUP BY table_name
),
deps AS (
    SELECT 
        ccu.table_name AS parent,
        tc.table_name AS child,
        ROW_NUMBER() OVER (PARTITION BY tc.table_name ORDER BY ccu.table_name) AS rn
    FROM information_schema.table_constraints tc
    JOIN information_schema.constraint_column_usage ccu 
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.constraint_type = 'FOREIGN KEY' 
      AND tc.table_name != ccu.table_name
),
tables_with_id AS (
    SELECT 
        table_name,
        depth,
        ROW_NUMBER() OVER (ORDER BY depth) AS id
    FROM min_depth
)
SELECT 
    t.id AS "ID",
    t.table_name AS "Название таблицы",
    p1.id AS "parent_1",
    p2.id AS "parent_2"
FROM tables_with_id t
LEFT JOIN deps d1 ON t.table_name = d1.child AND d1.rn = 1
LEFT JOIN tables_with_id p1 ON d1.parent = p1.table_name
LEFT JOIN deps d2 ON t.table_name = d2.child AND d2.rn = 2
LEFT JOIN tables_with_id p2 ON d2.parent = p2.table_name
ORDER BY t.id;
