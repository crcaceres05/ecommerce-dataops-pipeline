-- Resumen diario de órdenes — tabla principal del dashboard
-- Una fila = un día

with orders as (
    select * from {{ ref('int_orders_with_items') }}
),

daily as (
    select
        date_trunc('day', ordered_at)::date     as order_date,

        -- Volumen
        count(order_id)                         as total_orders,
        sum(total_items)                        as total_items_sold,

        -- Revenue
        round(sum(order_total), 2)              as gross_revenue,
        round(avg(order_total), 2)              as avg_order_value,
        round(sum(total_freight), 2)            as total_freight_revenue,

        -- Calidad de entrega
        count(case when order_status = 'delivered'
                   then 1 end)                  as delivered_orders,
        count(case when delivered_on_time = true
                   then 1 end)                  as on_time_deliveries,
        round(
            100.0 * count(case when delivered_on_time = true then 1 end)
            / nullif(count(case when order_status = 'delivered' then 1 end), 0),
            2
        )                                       as on_time_pct,

        -- Timing promedio
        round(avg(case when days_to_deliver > 0
                       then days_to_deliver end), 1) as avg_delivery_days

    from orders
    group by date_trunc('day', ordered_at)::date
)

select * from daily
order by order_date
