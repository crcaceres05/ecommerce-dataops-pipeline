-- Une órdenes con sus items y calcula totales por orden

with orders as (
    select * from {{ ref('stg_orders') }}
),

items as (
    select
        order_id,
        count(order_item_id)            as total_items,
        sum(item_price)                 as subtotal,
        sum(freight_cost)               as total_freight,
        sum(item_price + freight_cost)  as order_total
    from {{ ref('stg_order_items') }}
    group by order_id
),

customers as (
    select * from {{ ref('stg_customers') }}
),

joined as (
    select
        o.order_id,
        o.customer_id,
        o.order_status,
        o.ordered_at,
        o.approved_at,
        o.shipped_at,
        o.delivered_at,
        o.estimated_delivery_at,

        -- Métricas de timing
        datediff('day', o.ordered_at, o.delivered_at)           as days_to_deliver,
        datediff('day', o.ordered_at, o.estimated_delivery_at)  as days_estimated,

        -- Flag: ¿llegó a tiempo?
        case
            when o.delivered_at <= o.estimated_delivery_at then true
            else false
        end                                                     as delivered_on_time,

        -- Items y montos
coalesce(i.total_items, 0)      as total_items,
        coalesce(i.subtotal, 0)         as subtotal,
        coalesce(i.total_freight, 0)    as total_freight,
        coalesce(i.order_total, 0)      as order_total,

        -- Datos del cliente
        c.city                  as customer_city,
        c.state                 as customer_state

    from orders o
    left join items i
        on o.order_id = i.order_id
    left join customers c
        on o.customer_id = c.customer_id
)

select * from joined
