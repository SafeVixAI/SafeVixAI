// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team

import { render, screen, fireEvent } from '@testing-library/react'
import React from 'react'
import { DataTable, Column } from '../ui/DataTable'

interface TestItem {
  id: number
  name: string
  age: number
}

const columns: Column<TestItem>[] = [
  { key: 'name', header: 'Name', sortable: true, filterable: true },
  { key: 'age', header: 'Age', sortable: true, align: 'right' },
]

const data: TestItem[] = [
  { id: 1, name: 'Alice', age: 30 },
  { id: 2, name: 'Bob', age: 25 },
  { id: 3, name: 'Charlie', age: 35 },
]

const keyExtractor = function(item: TestItem) { return String(item.id) }

describe('DataTable', function() {
  it('renders data rows', function() {
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor }))
    expect(screen.getByText('Alice')).toBeTruthy()
    expect(screen.getByText('Bob')).toBeTruthy()
    expect(screen.getByText('Charlie')).toBeTruthy()
  })

  it('renders headers', function() {
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor }))
    expect(screen.getByText('Name')).toBeTruthy()
    expect(screen.getByText('Age')).toBeTruthy()
  })

  it('shows loading skeleton when loading', function() {
    const { container } = render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor, loading: true }))
    expect(screen.getByRole('status')).toBeTruthy()
    expect(container.querySelector('.animate-pulse')).toBeTruthy()
  })

  it('shows empty message when no data', function() {
    render(React.createElement(DataTable, { columns: columns, data: [], keyExtractor: keyExtractor, emptyMessage: 'Nothing here' }))
    expect(screen.getByText('Nothing here')).toBeTruthy()
  })

  it('sets aria-sort on sortable header click', function() {
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor }))
    const nameHeader = screen.getByText('Name')
    expect(nameHeader.closest('th')?.getAttribute('aria-sort')).toBeFalsy()
    fireEvent.click(nameHeader)
    expect(nameHeader.closest('th')?.getAttribute('aria-sort')).toBe('ascending')
    fireEvent.click(nameHeader)
    expect(nameHeader.closest('th')?.getAttribute('aria-sort')).toBe('descending')
  })

  it('renders filter input when column has filterable', function() {
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor }))
    expect(screen.getByLabelText('Filter table')).toBeTruthy()
  })

  it('filters data when typing in filter', function() {
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor }))
    const input = screen.getByLabelText('Filter table') as HTMLInputElement
    fireEvent.change(input, { target: { value: 'Bob' } })
    expect(screen.getByText('Bob')).toBeTruthy()
    expect(screen.queryByText('Alice')).toBeNull()
  })

  it('shows pagination when data exceeds pageSize', function() {
    const manyItems: TestItem[] = Array.from({ length: 25 }, function(_, i) {
      return { id: i, name: 'Item ' + i, age: 20 + i }
    })
    render(React.createElement(DataTable, { columns: columns, data: manyItems, keyExtractor: keyExtractor, pageSize: 10 }))
    expect(screen.getByLabelText('Pagination')).toBeTruthy()
    expect(screen.getByText('25 results')).toBeTruthy()
  })

  it('supports row selection', function() {
    let selection = new Set<string>()
    const onSelectionChange = jest.fn(function(keys: Set<string>) { selection = keys })
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor, selectable: true, selectedKeys: selection, onSelectionChange: onSelectionChange }))
    const checkboxes = screen.getAllByRole('checkbox')
    expect(checkboxes.length).toBe(4)
    fireEvent.click(checkboxes[1])
    expect(selection.size).toBe(1)
  })

  it('selects all when header checkbox clicked', function() {
    let selection = new Set<string>()
    const onSelectionChange = jest.fn(function(keys: Set<string>) { selection = keys })
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor, selectable: true, selectedKeys: selection, onSelectionChange: onSelectionChange }))
    fireEvent.click(screen.getByLabelText('Select all rows'))
    expect(selection.size).toBe(3)
  })

  it('deselects all when all rows already selected', function() {
    let selection = new Set<string>(['1', '2', '3'])
    const onSelectionChange = jest.fn(function(keys: Set<string>) { selection = keys })
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor, selectable: true, selectedKeys: selection, onSelectionChange: onSelectionChange }))
    fireEvent.click(screen.getByLabelText('Select all rows'))
    expect(selection.size).toBe(0)
  })

  it('calls onRowClick when row is clicked', function() {
    const onRowClick = jest.fn()
    render(React.createElement(DataTable, { columns: columns, data: data, keyExtractor: keyExtractor, onRowClick: onRowClick }))
    fireEvent.click(screen.getByText('Alice'))
    expect(onRowClick).toHaveBeenCalledWith(data[0])
  })

  it('navigates pages with prev/next buttons', function() {
    const manyItems: TestItem[] = Array.from({ length: 25 }, function(_, i) { return { id: i, name: 'Item ' + i, age: 20 + i } })
    render(React.createElement(DataTable, { columns: columns, data: manyItems, keyExtractor: keyExtractor, pageSize: 10 }))
    expect(screen.getByText('Item 0')).toBeTruthy()
    fireEvent.click(screen.getByLabelText('Next page'))
    expect(screen.getByText('Item 10')).toBeTruthy()
    fireEvent.click(screen.getByLabelText('Previous page'))
    expect(screen.getByText('Item 0')).toBeTruthy()
  })

  it('shows page number buttons when many pages', function() {
    const manyItems: TestItem[] = Array.from({ length: 100 }, function(_, i) { return { id: i, name: 'Item ' + i, age: 20 + i } })
    render(React.createElement(DataTable, { columns: columns, data: manyItems, keyExtractor: keyExtractor, pageSize: 10 }))
    expect(screen.getByLabelText('Page 1')).toBeTruthy()
    expect(screen.getByLabelText('Page 2')).toBeTruthy()
    fireEvent.click(screen.getByLabelText('Page 2'))
    expect(screen.getByLabelText('Page 2')?.getAttribute('aria-current')).toBe('page')
  })
})
