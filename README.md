# Product Variant Sale Dates

This Odoo addon module allows you to set start and end sale dates for product attribute values (like "Early Adopter", "Standard", etc.). All variants using those attribute values will inherit the sale dates and be automatically hidden from the website after their end date.

## Features

- **Attribute-Level Control**: Set sale dates at the attribute value level (e.g., "Early Adopter", "Standard")
- **Automatic Inheritance**: All variants using an attribute value inherit its sale dates
- **Smart Date Logic**: When variants have multiple attributes, the most restrictive dates are used
- **Automatic Hiding**: Variants are automatically hidden from the website after their end date
- **Visual Indicators**: Sale period information is displayed on product pages and in product lists
- **Purchase Prevention**: Expired variants cannot be added to cart
- **Admin Interface**: Easy management through attribute value and product form views

## Perfect for VIP Tickets and Limited Releases

This module is ideal for scenarios like:

- **VIP Tickets** with "Early Adopter" and "Standard" release periods
- **Limited Edition Products** with seasonal availability
- **Event Tickets** with different access periods
- **Promotional Items** with time-limited availability

## Installation

1. Copy this module to your Odoo addons directory
2. Update the addon list in Odoo
3. Install the "Product Variant Sale Dates" module

## Usage

### Setting Sale Dates for Attribute Values

1. Go to **Inventory > Products > Attributes**
2. Open an attribute (e.g., "Release")
3. Edit the attribute values (e.g., "Early Adopter", "Standard")
4. Set the sale dates for each value:
   - **Sale Start Date**: When this attribute value becomes available
   - **Sale End Date**: When this attribute value stops being available
5. Save the attribute value

### How It Works

- **Early Adopter** attribute value: Available Jan 1 - Mar 31
- **Standard** attribute value: Available Feb 1 - Apr 30
- All variants with "Early Adopter" will be available Jan 1 - Mar 31
- All variants with "Standard" will be available Feb 1 - Apr 30

### Multiple Attributes

When a variant has multiple attributes with sale dates:

- **Start Date**: Uses the latest (most restrictive) start date
- **End Date**: Uses the earliest (most restrictive) end date

Example:

- Color "Red": Available Jan 1 - Dec 31
- Size "Small": Available Mar 1 - May 31
- Red Small variant: Available Mar 1 - May 31 (most restrictive)

### Viewing Sale Information

- **Product Pages**: Sale period information is displayed prominently on the website
- **Product Lists**: Variants show their sale period as badges
- **Admin Views**: Sale dates are visible in attribute value and product form views

### Automatic Behavior

- Variants are automatically hidden from the website when their sale period expires
- Customers cannot add expired variants to their cart
- Sale period information is shown to help customers understand availability

## Technical Details

### Models Extended

- `product.attribute.value`: Added sale date fields for attribute values
- `product.product`: Added computed fields that inherit from attribute values
- `product.template`: Modified variant filtering to exclude expired variants

### Key Fields

**On `product.attribute.value`:**

- `sale_start_date`: Datetime field for when this attribute value becomes available
- `sale_end_date`: Datetime field for when this attribute value stops being available
- `is_sale_period_active`: Computed boolean indicating if currently available
- `sale_period_info`: Human-readable sale period information

**On `product.product` (computed from attribute values):**

- `sale_start_date`: Inherited from most restrictive attribute value
- `sale_end_date`: Inherited from most restrictive attribute value
- `is_sale_period_active`: Computed based on inherited dates
- `sale_period_info`: Computed based on inherited dates

### Website Integration

- Product pages show sale period information
- Variant selection hides expired options
- Product lists filter out expired variants
- Cart functionality prevents adding expired variants

## Dependencies

- `product`: Core product management
- `website_sale`: E-commerce functionality

## License

Other OSI approved license

## Author

Eventiva (www.eventiva.com)
