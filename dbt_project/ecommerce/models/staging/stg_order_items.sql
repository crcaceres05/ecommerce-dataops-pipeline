-- Una fila = un item dentro de una orden

with source as (
    select * from raw_order_items
),

renamed as (
    select
        order_id,
        order_item_id,
        product_id,
        seller_id,
        strptime(shipping_limit_date,
                 '%Y-%m-%d %H:%M:%S')   as shipping_limit_at,
        price                           as item_price,
        freight_value                   as freight_cost
    from source
)

select * from renamed
