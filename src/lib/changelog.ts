export type ChangelogEntry = {
    semver: string;
    releaseNotes: string;
    date: string;
};

const CHANGELOG: ChangelogEntry[] = [
    {
        semver: '0.0.3',
        releaseNotes: 'Added account values over time graph to the dashboard.',
        date: '2025-12-15'
    },
    {
        semver: '0.0.2',
        releaseNotes: 'Upgraded all dependencies to latest versions.',
        date: '2025-11-08'
    },
    {
        semver: '0.0.1',
        releaseNotes: 'Initial release.',
        date: '2024-11-08'
    }
];

export const latestVersion = CHANGELOG[0];

export const getLatestEntries = (count: number) => CHANGELOG.slice(0, count);

export const hasMoreEntries = (count: number) => CHANGELOG.length > count;
