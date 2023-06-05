import pandas as pd

def process_order_data(file_path):
    try:
        # Read the CSV file into a DataFrame
        data = pd.read_csv(file_path)

        # Validate the columns in the CSV file
        if 'order_id' not in data.columns or 'product_id' not in data.columns:
            raise ValueError("Invalid column names in the CSV file.")

        # Initialize a dictionary to keep track of products and their coverage
        product_coverage = {}

        # Iterate over each row in the DataFrame
        for _, row in data.iterrows():
            # Convert the values to integers if possible
            try:
                order_id = int(row['order_id'])
                product_id = int(row['product_id'])
            except ValueError:
                raise ValueError("Invalid order_id or product_id in the CSV file.")

            # Rest of the code remains the same...

            # Check if the product is already in the coverage dictionary
            if product_id in product_coverage:
                # If it is, increment the coverage count for that product
                product_coverage[product_id]['coverage'] += 1
            else:
                # If it's not, add it to the coverage dictionary
                product_coverage[product_id] = {
                    'coverage': 1,
                    'additional_coverage': 0,
                    'cumulative_coverage': 0
                }

            # Iterate over the products before the current one
            for prev_product_id in product_coverage.keys():
                if prev_product_id != product_id:
                    # Increment the additional coverage count for each previous product
                    product_coverage[prev_product_id]['additional_coverage'] += 1

        # Calculate the cumulative coverage for each product
        cumulative_coverage = 0
        for product_id in product_coverage:
            product_coverage[product_id]['cumulative_coverage'] = (
                product_coverage[product_id]['coverage'] +
                product_coverage[product_id]['additional_coverage']
            )
            # Update the cumulative coverage count
            cumulative_coverage = max(
                cumulative_coverage, product_coverage[product_id]['cumulative_coverage']
            )

        # Create a DataFrame from the product_coverage dictionary
        result = pd.DataFrame.from_dict(product_coverage, orient='index')
        result.index.name = 'Product_id'
        result.sort_values(by='additional_coverage', ascending=False, inplace=True)

        return result[['additional_coverage', 'cumulative_coverage']]

    except (FileNotFoundError, pd.errors.EmptyDataError) as e:
        print(f"Error: {e}")
        return None
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return None
    except Exception as ex:
        print(f"An unexpected error occurred: {ex}")
        return None


def main():
    file_path = 'order_data.csv'
    result = process_order_data(file_path)
    if result is not None:
        print(result)

if __name__ == '__main__':
    main()
