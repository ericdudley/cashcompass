<script lang="ts">
	import { onDestroy } from 'svelte';
	import Pencil from 'virtual:icons/mdi/pencil';
	import IconParkOutlineEnterKey from 'virtual:icons/icon-park-outline/enter-key';
	import KeyboardEsc from 'virtual:icons/mdi/keyboard-esc';

	let { value, onSave }: { value: string; onSave: (value: string) => void } = $props();

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
	function handleKeydown(event) {
		if (event.key === 'Enter') {
			save();
		} else if (event.key === 'Escape') {
			cancel();
		}
	}

	// Save if clicked outside of the input
	function handleClickOutside(event) {
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
			class="w-96 absolute top-0 left-0 right-0 flex items-center transform translate-y-[calc(-100%-0.5rem)]"
		>
			<button onclick={save} class="flex-1 btn btn-sm btn-success">
				Save
				<IconParkOutlineEnterKey />
			</button>
			<button onclick={cancel} class="flex-1 btn btn-sm btn-error ml-2">
				Cancel
				<KeyboardEsc />
			</button>
		</div>
	</div>
{:else}
	<span
		class="editable-field flex items-center gap-1 hover:cursor-pointer hover:border-b-2 hover:border-b-primary focus:border-b-2 focus:border-b-primary"
		onclick={enableEdit}
		tabindex="0"
		onfocus={enableEdit}
	>
		<span>
			{value}
		</span>
		<span>
			<Pencil />
		</span>
	</span>
{/if}

<style>
	.edit-icon {
		opacity: 0;
		transition: opacity 0.3s ease;
	}

	.editable-field:hover .edit-icon {
		opacity: 1;
	}
</style>
