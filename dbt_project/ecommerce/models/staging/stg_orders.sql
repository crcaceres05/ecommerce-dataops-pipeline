-- Limpieza y tipado de la tabla de órdenes
-- Una fila = una orden

with source as (
    select * from raw_orders
),

renamed as (
    select
        order_id,
        customer_id,

        -- Estandariza el status como texto limpio
        lower(trim(order_status))                           as order_status,

        -- Convierte timestamps de texto a tipo timestamp
        strptime(order_purchase_timestamp,
                 '%Y-%m-%d %H:%M:%S')                      as ordered_at,
        strptime(order_approved_at,
                 '%Y-%m-%d %H:%M:%S')                      as approved_at,
        strptime(order_delivered_carrier_date,
                 '%Y-%m-%d %H:%M:%S')                      as shipped_at,
        strptime(order_delivered_customer_date,
                 '%Y-%m-%d %H:%M:%S')                      as delivered_at,
        strptime(order_estimated_delivery_date,
                 '%Y-%m-%d %H:%M:%S')                      as estimated_delivery_at

    from source
)

select * from renamed
