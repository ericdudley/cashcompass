<script lang="ts">
	import { onDestroy } from 'svelte';
	import Pencil from 'virtual:icons/mdi/pencil';
	import IconParkOutlineEnterKey from 'virtual:icons/icon-park-outline/enter-key';
	import KeyboardEsc from 'virtual:icons/mdi/keyboard-esc';

	let {
		value,
		onSave,
		showEditIcon
	}: { value: string; onSave: (value: string) => void; showEditIcon?: boolean } = $props();

	// Internal state to handle temporary editing state
	let isEditing = $state(false);
	let tempValue = $state(value);

	// Enable editing mode
	function enableEdit() {
		tempValue = value;
		isEditing = true;
	}

	// Save the temporary value
	function save() {
		value = tempValue;
		isEditing = false;
		onSave(value);
	}

	// Cancel editing and reset temp value
	function cancel() {
		tempValue = value;
		isEditing = false;
	}

	// Handle Enter/Escape keys during editing
	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			save();
		} else if (event.key === 'Escape') {
			cancel();
		}
	}

	// Save if clicked outside of the input
	function handleClickOutside(event: MouseEvent) {
		if (event.target !== event.currentTarget) {
			return;
		}
		save();
	}

	// Clean up event listeners when component is destroyed
	onDestroy(() => {
		window.removeEventListener('click', handleClickOutside);
	});
</script>

{#if isEditing}
	<div class="relative">
		<!-- svelte-ignore a11y_autofocus -->
		<input
			bind:value={tempValue}
			onkeydown={handleKeydown}
			class="input input-sm input-bordered w-full"
			autofocus
			onblur={() => {
				save();
			}}
		/>
		<div
			class="absolute top-0 left-1/2 flex items-center transform translate-y-[calc(-100%-0.5rem)] translate-x-[-50%] gap-2 z-[100]"
		>
			<button onclick={save} class="flex-1 btn btn-sm btn-success flex-nowrap">
				Save
				<IconParkOutlineEnterKey />
			</button>
			<button onclick={cancel} class="flex-1 btn btn-sm btn-error ml-2 flex-nowrap">
				Cancel
				<KeyboardEsc />
			</button>
		</div>
	</div>
{:else}
	<button
		class="editable-field flex items-center gap-1 hover:cursor-pointer hover:border-b-2 hover:border-b-primary focus:border-b-2 focus:border-b-primary"
		onclick={enableEdit}
		tabindex="0"
		onfocus={enableEdit}
	>
		<span>
			{value}
		</span>
		{#if !!showEditIcon}
			<span>
				<Pencil />
			</span>
		{/if}
	</button>
{/if}
