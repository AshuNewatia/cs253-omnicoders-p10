#ifndef TRIAGE_STRUCTURE_A_LOCATOR_H
#define TRIAGE_STRUCTURE_A_LOCATOR_H

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <utility>
#include <vector>

struct twin {
    int ID;
    std::size_t address;

    twin(int id, std::size_t index) : ID(id), address(index) {}
};

class LookUp {
private:
    enum class SlotState : unsigned char { Empty, Occupied, Deleted };

    struct Slot {
        int id = 0;
        std::size_t index = 0;
        SlotState state = SlotState::Empty;
    };

    static const std::size_t INITIAL_CAPACITY = 1024;
    std::vector<Slot> slots;
    std::size_t live_count = 0;
    std::size_t used_count = 0;

    std::size_t hash_id(int id) const {
        // Mix the full 32-bit representation; negative IDs are valid too.
        std::uint32_t value = static_cast<std::uint32_t>(id);
        value ^= value >> 16;
        value *= 0x7feb352dU;
        value ^= value >> 15;
        value *= 0x846ca68bU;
        value ^= value >> 16;
        return static_cast<std::size_t>(value) % slots.size();
    }

    std::size_t find_slot(int id) const {
        const std::size_t start = hash_id(id);
        for (std::size_t step = 0; step < slots.size(); ++step) {
            const std::size_t slot = (start + step) % slots.size();
            if (slots[slot].state == SlotState::Empty) return slots.size();
            if (slots[slot].state == SlotState::Occupied && slots[slot].id == id)
                return slot;
        }
        return slots.size();
    }

    void insert_without_resize(int id, std::size_t index) {
        const std::size_t start = hash_id(id);
        std::size_t first_deleted = slots.size();
        for (std::size_t step = 0; step < slots.size(); ++step) {
            const std::size_t slot = (start + step) % slots.size();
            if (slots[slot].state == SlotState::Deleted && first_deleted == slots.size())
                first_deleted = slot;
            if (slots[slot].state == SlotState::Empty) {
                const std::size_t target = first_deleted == slots.size() ? slot : first_deleted;
                if (first_deleted == slots.size()) ++used_count;
                slots[target].id = id;
                slots[target].index = index;
                slots[target].state = SlotState::Occupied;
                ++live_count;
                return;
            }
        }
        if (first_deleted != slots.size()) {
            slots[first_deleted].id = id;
            slots[first_deleted].index = index;
            slots[first_deleted].state = SlotState::Occupied;
            ++live_count;
            return;
        }
        throw std::logic_error("locator has no free slot");
    }

    void rehash(std::size_t new_capacity) {
        std::vector<Slot> old_slots;
        old_slots.swap(slots);
        slots.assign(new_capacity, Slot{});
        live_count = 0;
        used_count = 0;
        for (const Slot& slot : old_slots) {
            if (slot.state == SlotState::Occupied)
                insert_without_resize(slot.id, slot.index);
        }
    }

public:
    LookUp() : slots(INITIAL_CAPACITY) {}

    bool contains(int id) const {
        return find_slot(id) != slots.size();
    }

    std::size_t find(int id) const {
        const std::size_t slot = find_slot(id);
        if (slot == slots.size()) throw std::out_of_range("patient ID not found in locator");
        return slots[slot].index;
    }

    void Insert(twin entry) {
        if (contains(entry.ID))
            throw std::invalid_argument("patient ID is already present in locator");

        if ((used_count + 1) * 10 >= slots.size() * 7) {
            const std::size_t new_capacity =
                (live_count + 1) * 10 >= slots.size() * 7
                    ? slots.size() * 2
                    : slots.size();
            rehash(new_capacity);
        }
        insert_without_resize(entry.ID, entry.address);
    }

    void Delete(int id) {
        const std::size_t slot = find_slot(id);
        if (slot == slots.size()) throw std::out_of_range("patient ID not found in locator");
        slots[slot].state = SlotState::Deleted;
        --live_count;
    }

    void interchange(int first_id, int second_id) {
        const std::size_t first = find_slot(first_id);
        const std::size_t second = find_slot(second_id);
        if (first == slots.size() || second == slots.size())
            throw std::out_of_range("locator entry missing during heap swap");
        std::swap(slots[first].index, slots[second].index);
    }
};

#endif
