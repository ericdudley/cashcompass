import type { TimeoutID } from './types';

export function debounce<T>(getter: () => T, delay: number): () => T | undefined {
	let value = $state<T>();
	let timer: TimeoutID;
	$effect(() => {
		const newValue = getter(); // read here to subscribe to it
		clearTimeout(timer);
		timer = setTimeout(() => (value = newValue), delay);
		return () => clearTimeout(timer);
	});
	return () => value;
}
