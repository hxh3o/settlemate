import { useEffect, useMemo, useState } from 'react';
import { MaterialReactTable, useMaterialReactTable } from 'material-react-table';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import { API, authHeaders } from '../api';

const TripTable = () => {
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
                const response = await fetch(`${API}/getTripsData`, {
                    method: 'GET',
                    headers: authHeaders(),
                });
				const json = await response.json();
				if (json.success) {
					setData(json.data);
					setRowCount(json.data.length);
					// console.log(json.invites);
					if (json.invites > 0) toast.info('You have Trip Invites!', {});
					if (json.invites > 0) console.log('yes');
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
		fetchData();
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, []);

	const columns = useMemo(
		() => [
			{
				accessorKey: 'name',
				header: 'Trip Name',
			},
			{
				accessorKey: 'owner.name',
				header: 'Trip Owner',
			},
			{
				accessorFn: originalRow => new Date(originalRow.created_at || originalRow.createdAt || originalRow.dateCreated),
				id: 'created_at',
				header: 'Created On',
				Cell: ({ cell }) =>
					new Date(cell.getValue()).toLocaleString('en-US', {
						year: 'numeric',
						month: 'short',
						day: 'numeric',
						hour: '2-digit',
						minute: '2-digit',
						hour12: true,
					}),
			},
			{
				accessorFn: originalRow => new Date(originalRow.last_edited || originalRow.updated_at || originalRow.lastEdited),
				id: 'last_edited',
				header: 'Last Modified',
				Cell: ({ cell }) =>
					new Date(cell.getValue()).toLocaleString('en-US', {
						year: 'numeric',
						month: 'short',
						day: 'numeric',
						hour: '2-digit',
						minute: '2-digit',
						hour12: true,
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
				// Use original data's UUID when navigating
				navigate('/trip', { state: { tripid: row.original.id } });
			},
			sx: {
				cursor: 'pointer',
			},
		}),
	});

	return <MaterialReactTable table={table} />;
};

export default TripTable;
