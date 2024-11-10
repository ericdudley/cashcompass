import { startOfDay, parseISO } from 'date-fns';

export function currentIso8601() {
	return new Date().toISOString();
}

export function formatYyyyMMDd(date: Date) {
	return date.toISOString().slice(0, 10);
}

export function getIso8601AtMidnight(yyyyMMDd: string) {
	return startOfDay(parseISO(yyyyMMDd)).toISOString();
}
