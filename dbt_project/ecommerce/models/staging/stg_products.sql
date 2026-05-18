with source as (
    select * from raw_products
),

renamed as (
    select
        product_id,
        -- Normaliza categoría: reemplaza guiones bajos por espacios
        replace(
            lower(trim(product_category_name)), '_', ' '
        )                                   as product_category,
        product_name_lenght                 as product_name_length,
        product_description_lenght          as product_description_length,
        product_photos_qty                  as product_photos_count,
        product_weight_g                    as weight_grams,
        product_length_cm                   as length_cm,
        product_height_cm                   as height_cm,
        product_width_cm                    as width_cm
    from source
)

select * from renamed
