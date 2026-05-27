USE master;
GO

-- 1. DROP THE CHILD TABLE FIRST (This breaks the FK links)
IF OBJECT_ID('[dbo].[fact_orders]', 'U') IS NOT NULL
    DROP TABLE [dbo].[fact_orders];
GO

-- 2. NOW DROP THE PARENT DIMENSION TABLES
IF OBJECT_ID('[dbo].[dim_customers]', 'U') IS NOT NULL
    DROP TABLE [dbo].[dim_customers];
GO

IF OBJECT_ID('[dbo].[dim_products]', 'U') IS NOT NULL
    DROP TABLE [dbo].[dim_products];
GO

IF OBJECT_ID('[dbo].[dim_location]', 'U') IS NOT NULL
    DROP TABLE [dbo].[dim_location];
GO

IF OBJECT_ID('[dbo].[dim_time]', 'U') IS NOT NULL
    DROP TABLE [dbo].[dim_time];
GO

-- 3. DROP STAGING AND OTHER REMNANT TABLES
IF OBJECT_ID('[dbo].[stg_customers]', 'U') IS NOT NULL DROP TABLE [dbo].[stg_customers];
IF OBJECT_ID('[dbo].[stg_orders]', 'U') IS NOT NULL DROP TABLE [dbo].[stg_orders];
IF OBJECT_ID('[dbo].[stg_order_items]', 'U') IS NOT NULL DROP TABLE [dbo].[stg_order_items];
IF OBJECT_ID('[dbo].[stg_products]', 'U') IS NOT NULL DROP TABLE [dbo].[stg_products];
IF OBJECT_ID('[dbo].[customers]', 'U') IS NOT NULL DROP TABLE [dbo].[customers];
IF OBJECT_ID('[dbo].[products]', 'U') IS NOT NULL DROP TABLE [dbo].[products];
IF OBJECT_ID('[dbo].[orders]', 'U') IS NOT NULL DROP TABLE [dbo].[orders];
IF OBJECT_ID('[dbo].[order_items]', 'U') IS NOT NULL DROP TABLE [dbo].[order_items];
GO