import { useEffect, useMemo, useState } from 'react';
import { MaterialReactTable, useMaterialReactTable } from 'material-react-table';
import { useNavigate } from 'react-router-dom';
import { API, authHeaders } from '../api';

const TransactionTable = ({ tripid }) => {
	const [data, setData] = useState([]);
	const [isError, setIsError] = useState(false);
	const [isLoading, setIsLoading] = useState(false);
	const [isRefetching, setIsRefetching] = useState(false);
	const [rowCount, setRowCount] = useState(0);

	const [columnFilters, setColumnFilters] = useState([]);
	const [globalFilter, setGlobalFilter] = useState('');
	const [sorting, setSorting] = useState([]);
	const [pagination, setPagination] = useState({
		pageIndex: 0,
		pageSize: 10,
	});

	useEffect(() => {
		const fetchData = async () => {
			if (!data.length) {
				setIsLoading(true);
			} else {
				setIsRefetching(true);
			}

			try {
				const response = await fetch(`${API}/getTransactions?tripid=${encodeURIComponent(tripid)}`, {
					method: 'GET',
					headers: authHeaders(),
				});
				const json = await response.json();
				if (json.success) {
					const items = Array.isArray(json.data) ? json.data : Array.isArray(json.data?.transactions) ? json.data.transactions : [];
					setData(items);
					setRowCount(items.length);
					if (json.newAuthToken) localStorage.setItem('authToken', json.newAuthToken);
				} else {
					localStorage.removeItem('authToken');
					localStorage.setItem('forcedLogOut', true);
					navigate('/profile');
				}
			} catch (error) {
				setIsError(true);
				console.error('Error fetching userData :', error);
				return;
			}
			setIsError(false);
			setIsLoading(false);
			setIsRefetching(false);
		};
		if (tripid) fetchData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [tripid]);

	const columns = useMemo(
		() => [
			{
				accessorKey: 'amount',
				header: 'Amount',
				Cell: ({ cell }) => Number(cell.getValue()).toFixed(2),
			},
			{
				accessorKey: 'name',
				header: 'Reason',
			},
			{
				accessorKey: 'paid_by.name',
				header: 'Paid By',
			},
			{
				accessorFn: originalRow => new Date(originalRow.created_at || originalRow.createdAt || originalRow.dateCreated),
				id: 'created_at',
				header: 'Created On',
				Cell: ({ cell }) =>
					new Date(cell.getValue()).toLocaleString('en-US', {
						year: 'numeric',
						month: 'long',
						day: 'numeric',
						hour: '2-digit',
						minute: '2-digit',
						second: '2-digit',
					}),
			},
			{
				accessorFn: originalRow => new Date(originalRow.updated_at || originalRow.lastEdited),
				id: 'updated_at',
				header: 'Last Modified',
				Cell: ({ cell }) =>
					new Date(cell.getValue()).toLocaleString('en-US', {
						year: 'numeric',
						month: 'long',
						day: 'numeric',
						hour: '2-digit',
						minute: '2-digit',
						second: '2-digit',
					}),
			},
		],
		[]
	);
	const navigate = useNavigate();
	const table = useMaterialReactTable({
		columns,
		data,
		enableRowSelection: false,
		enableColumnFilters: false,
		getRowId: row => row.id,
		initialState: { showColumnFilters: false },
		manualFiltering: false,
		manualPagination: false,
		manualSorting: false,
		muiToolbarAlertBannerProps: isError
			? {
					color: 'error',
					children: 'Error loading data',
			  }
			: undefined,
		onColumnFiltersChange: setColumnFilters,
		onGlobalFilterChange: setGlobalFilter,
		onPaginationChange: setPagination,
		onSortingChange: setSorting,
		rowCount,
		state: {
			columnFilters,
			globalFilter,
			isLoading,
			pagination,
			showAlertBanner: isError,
			showProgressBars: isRefetching,
			sorting,
		},
		muiTableBodyRowProps: ({ row }) => ({
			onClick: () => {
				navigate('/transaction', {
					state: { transactionid: row.id, tripid: tripid },
				});
			},
			sx: {
				cursor: 'pointer',
			},
		}),
	});

	return <MaterialReactTable table={table} />;
};

export default TransactionTable;
