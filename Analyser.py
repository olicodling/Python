import pandas as pd
import glob
import os
from collections import defaultdict

def load_data(folder_path='.'):
    """
    Load and combine all CSV files from the specified folder.
    Looks for files matching pattern: *.csv
    """
    csv_files = glob.glob(os.path.join(folder_path, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {folder_path}")
        return None
    
    print(f"Found {len(csv_files)} CSV file(s):")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")
    
    # Read and combine all CSVs
    dfs = []
    for file in csv_files:
        df = pd.read_csv(file)
        dfs.append(df)
        print(f"  Loaded {len(df)} rows from {os.path.basename(file)}")
    
    combined_df = pd.concat(dfs, ignore_index=True)
    print(f"\nTotal rows loaded: {len(combined_df)}")
    
    # Clean column names (remove extra spaces)
    combined_df.columns = combined_df.columns.str.strip()
    
    return combined_df

def analyze_check_coverage(df):
    """
    Analyze which customers can be migrated based on checks.
    Returns prioritized list of checks to implement.
    """
    # Group by customer to get all checks they need
    customer_checks = df.groupby('Customer')['Check name'].apply(set).to_dict()
    
    print(f"\nTotal unique customers: {len(customer_checks)}")
    print(f"Total unique checks: {df['Check name'].nunique()}")
    print(f"Total orders: {df['Order number'].nunique()}")
    
    # Track which customers are already covered
    covered_customers = set()
    supported_checks = set()
    priority_list = []
    
    # Greedy algorithm: keep adding checks that cover the most new customers
    all_checks = set(df['Check name'].unique())
    
    iteration = 1
    while len(covered_customers) < len(customer_checks):
        best_check = None
        best_new_customers = set()
        
        # Find the check that covers the most uncovered customers
        for check in all_checks - supported_checks:
            # Find customers who would be fully covered if we add this check
            newly_covered = set()
            for customer, required_checks in customer_checks.items():
                if customer not in covered_customers:
                    # Check if adding this check would complete their requirements
                    if required_checks.issubset(supported_checks | {check}):
                        newly_covered.add(customer)
            
            if len(newly_covered) > len(best_new_customers):
                best_check = check
                best_new_customers = newly_covered
        
        if best_check is None:
            break
        
        # Add the best check
        supported_checks.add(best_check)
        covered_customers.update(best_new_customers)
        
        # Calculate stats for this check
        check_order_count = len(df[df['Check name'] == best_check]['Order number'].unique())
        check_customer_count = len(df[df['Check name'] == best_check]['Customer'].unique())
        
        priority_list.append({
            'Priority': iteration,
            'Check Name': best_check,
            'New Customers Covered': len(best_new_customers),
            'Cumulative Customers': len(covered_customers),
            'Coverage %': f"{len(covered_customers) / len(customer_checks) * 100:.1f}%",
            'Orders Using Check': check_order_count,
            'Customers Using Check': check_customer_count
        })
        
        iteration += 1
        
        # Stop if we're getting minimal returns (optional)
        if len(best_new_customers) == 0:
            break
    
    return pd.DataFrame(priority_list), customer_checks, covered_customers

def analyze_check_combinations(df, top_n=20):
    """
    Find the most common check combinations (bundles).
    """
    # Group checks by order
    order_checks = df.groupby('Order number')['Check name'].apply(lambda x: tuple(sorted(x))).value_counts()
    
    print(f"\n{'='*80}")
    print(f"TOP {top_n} MOST COMMON CHECK COMBINATIONS")
    print(f"{'='*80}\n")
    
    for combo, count in order_checks.head(top_n).items():
        print(f"Frequency: {count} orders")
        print(f"Checks in bundle:")
        for check in combo:
            print(f"  - {check}")
        print()

def main():
    print("="*80)
    print("CHECK MIGRATION PRIORITY ANALYZER")
    print("="*80)
    
    # Option 1: Load from current directory
    # df = load_data()
    
    # Option 2: Specify a folder path
    folder = input("\nEnter folder path containing CSV files (or press Enter for current directory): ").strip()
    if not folder:
        folder = '.'
    
    df = load_data(folder)
    
    if df is None:
        return
    
    # Verify column names
    expected_cols = ['Customer', 'Order number', 'Check name']
    if not all(col in df.columns for col in expected_cols):
        print(f"\nError: CSV must contain columns: {expected_cols}")
        print(f"Found columns: {list(df.columns)}")
        return
    
    # Run analysis
    print("\n" + "="*80)
    print("RUNNING PRIORITY ANALYSIS...")
    print("="*80)
    
    priority_df, customer_checks, covered = analyze_check_coverage(df)
    
    # Display results
    print("\n" + "="*80)
    print("PRIORITIZED CHECK IMPLEMENTATION ORDER")
    print("="*80)
    print("\nThis shows which checks to implement in order to maximize customer migration.")
    print("Each check listed enables the 'New Customers Covered' to be migrated.\n")
    print(priority_df.to_string(index=False))
    
    # Save results to CSV
    output_file = 'check_priority_results.csv'
    priority_df.to_csv(output_file, index=False)
    print(f"\n✓ Results saved to: {output_file}")
    
    # Analyze common combinations
    analyze_check_combinations(df)
    
    # Summary stats
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Total customers: {len(customer_checks)}")
    print(f"Customers that can be migrated: {len(covered)}")
    print(f"Coverage: {len(covered) / len(customer_checks) * 100:.1f}%")
    print(f"Checks needed for full coverage: {len(priority_df)}")
    
    # Show diminishing returns point
    priority_df['Marginal Value'] = priority_df['New Customers Covered']
    top_20_pct_checks = int(len(priority_df) * 0.2)
    top_20_pct_coverage = priority_df.iloc[:top_20_pct_checks]['New Customers Covered'].sum()
    print(f"\nTop 20% of checks ({top_20_pct_checks} checks) cover {top_20_pct_coverage} customers")
    print(f"That's {top_20_pct_coverage / len(customer_checks) * 100:.1f}% of all customers")

if __name__ == "__main__":
    main()
