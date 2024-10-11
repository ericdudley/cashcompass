export type Category = {
    id: string;
    label: string;
}

export type Transaction = {
    id: string;
    date: Date;
    category: Category;
    amount: number;
    account: Account;
}

export type Account = {
    id: string;
    name: string;
    /**
     * If true, the account's balance will be tracked and included in net worth calculations.
     * If false, the account will not be included in net worth calculations
     */
    isIncludedInNetWorth: boolean;
}
