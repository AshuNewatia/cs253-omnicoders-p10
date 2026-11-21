#ifndef TRIAGE_STRUCTURE_A_H
#define TRIAGE_STRUCTURE_A_H

#include <cstddef>
#include <stdexcept>
#include <utility>
#include <vector>

#include "locator_for_structure_A.cpp"
#include "../../app/ITriageQueue.h"

#ifdef D5_COUNT_COMPARISONS
extern unsigned long long d5_comparisons;
#endif

class Min_Heap : public ITriageQueue {
private:
    LookUp table;
    std::vector<Patient> Heap;

    static bool comes_before(const Patient& a, const Patient& b) {
#ifdef D5_COUNT_COMPARISONS
        ++d5_comparisons;
#endif
        if (a.priority_key != b.priority_key)
            return a.priority_key < b.priority_key;
        if (a.arrival_time != b.arrival_time)
            return a.arrival_time < b.arrival_time;
        return a.id < b.id;
    }

    void swap_nodes(std::size_t first, std::size_t second) {
        if (first == second) return;
        std::swap(Heap[first], Heap[second]);
        table.interchange(Heap[first].id, Heap[second].id);
    }

    void sift_up(std::size_t index) {
        while (index > 0) {
            const std::size_t parent = (index - 1) / 2;
            if (!comes_before(Heap[index], Heap[parent])) return;
            swap_nodes(index, parent);
            index = parent;
        }
    }

    void sift_down(std::size_t index) {
        const std::size_t size = Heap.size();
        while (index < size / 2) {
            const std::size_t left = 2 * index + 1;
            const std::size_t right = left + 1;
            std::size_t smallest = left;
            if (right < size && comes_before(Heap[right], Heap[left]))
                smallest = right;
            if (!comes_before(Heap[smallest], Heap[index])) return;
            swap_nodes(index, smallest);
            index = smallest;
        }
    }

    Patient remove_at(std::size_t index) {
        const Patient removed = Heap[index];
        const std::size_t last = Heap.size() - 1;
        if (index != last) {
            swap_nodes(index, last);
        }
        table.Delete(removed.id);
        Heap.pop_back();

        if (index < Heap.size()) {
            if (index > 0 && comes_before(Heap[index], Heap[(index - 1) / 2]))
                sift_up(index);
            else
                sift_down(index);
        }
        return removed;
    }

public:
    Min_Heap() = default;

    explicit Min_Heap(const std::vector<Patient>& patients) {
        build_heap(patients);
    }

    void build_heap(const std::vector<Patient>& patients) override {
        // Build the locator first so duplicate IDs leave the current queue intact.
        std::vector<Patient> next_heap(patients);
        LookUp next_table;
        for (std::size_t i = 0; i < next_heap.size(); ++i)
            next_table.Insert(twin(next_heap[i].id, i));

        Heap.swap(next_heap);
        table = std::move(next_table);
        for (std::size_t i = Heap.size() / 2; i > 0; --i)
            sift_down(i - 1);
    }

    void insert(const Patient& patient) override {
        if (table.contains(patient.id))
            throw std::invalid_argument("patient ID is already live");

        const std::size_t index = Heap.size();
        table.Insert(twin(patient.id, index));
        try {
            Heap.push_back(patient);
        } catch (...) {
            table.Delete(patient.id);
            throw;
        }
        sift_up(index);
    }

    Patient peek() const {
        if (Heap.empty())
            throw std::out_of_range("cannot peek at an empty triage queue");
        return Heap[0];
    }

    Patient extract_min() override {
        if (Heap.empty())
            throw std::out_of_range("cannot extract from an empty triage queue");
        return remove_at(0);
    }

    void delete_patient(int id) override {
        const std::size_t index = table.find(id);
        remove_at(index);
    }

    void decrease_key(int id, long long new_key) override {
        const std::size_t index = table.find(id);
        if (new_key > Heap[index].priority_key)
            throw std::invalid_argument("decrease_key cannot increase the key");
        if (new_key == Heap[index].priority_key) return;

        Heap[index].priority_key = new_key;
        sift_up(index);
    }
};

#endif
