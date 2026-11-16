
from modules.properties import add_property, get_all_properties

print("Testing properties backend...")

properties = get_all_properties()
print("Existing properties:", len(properties))

for property_record in properties:
    print(property_record)

print("Properties backend loaded successfully.")

