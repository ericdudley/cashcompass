export function debounce<T>(getter: () => T, delay: number): () => T | undefined {
	let value = $state<T>();
	let timer: number;
	$effect(() => {
		const newValue = getter(); // read here to subscribe to it
		clearTimeout(timer);
		timer = setTimeout(() => (value = newValue), delay);
		return () => clearTimeout(timer);
	});
	return () => value;
}
