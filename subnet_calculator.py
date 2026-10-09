import ipaddress
import pandas as pd
import tabulate


# Function to check if a number is a power of two
def is_power_of_two(n):
    return n > 0 and (n & (n - 1)) == 0


# Main program inputs
ip = input("Enter the network ip address(example: 192.168.1.0): ")
subnet_mask = input(
    "Enter a network subnet mask(Example: 255.255.255.0 or 24): "
)

# Assemble IP address and subnet mask into a network
network = ipaddress.IPv4Network(f"{ip}/{subnet_mask}", strict=False)

# Total IP capacity for the base network
max_size = network.num_addresses
used_size = 0
counter = 1

# Data structures to store results
df = pd.DataFrame(
    [],
    columns=[
        "Network",
        "Start",
        "End",
        "Hosts",
        "Broadcast",
        "Subnet Mask",
        "Prefix",
    ],
)
sizes = []

# Collect subnet sizes until network capacity is reached or user exits
while used_size < max_size:
    user_input = input(
        f"Enter the Minimum size of subnet {counter}(Max size = {max_size - used_size}): "
    )

    # Allow user to exit or stop adding subnets by entering 0 or pressing Enter
    if not user_input or user_input.strip() == "0":
        break

    subnet_size = int(user_input)

    # Adjust subnet size up to the next power of 2
    while not is_power_of_two(subnet_size):
        subnet_size += 1

    # Check if size exceeds remaining space
    if used_size + subnet_size > max_size:
        print(f"Error: Subnet size exceeds remaining space ({max_size - used_size} IPs left).")
        break

    sizes.append(subnet_size)
    used_size += subnet_size
    counter += 1

# Process and calculate network ranges
current_ip = network.network_address

for size in sizes:
    # Determine CIDR prefix based on power-of-two size
    prefix = 32 - (size.bit_length() - 1)
    sub_net = ipaddress.IPv4Network(f"{current_ip}/{prefix}", strict=False)

    df.loc[len(df)] = [
        str(sub_net.network_address),
        str(sub_net.network_address + 1),
        str(sub_net.broadcast_address - 1),
        sub_net.num_addresses - 2,
        str(sub_net.broadcast_address),
        str(sub_net.netmask),
        f"/{prefix}",
    ]

    current_ip = sub_net.broadcast_address + 1

# Output formatted table
print("\n" + tabulate.tabulate(df, headers="keys", tablefmt="grid"))